# onodaga-e911

Scrape Onondaga county's computer aided dispatch (CAD) E911 events: http://wowbn.ongov.net/CADInet/app/events.jsp

## Quickstart

1. Install dependencies.

	Must have node and python3.6 installed.

	```
	pip3 install awscli
	pip3 install pipenv
	pipenv install
	npm install -g serverless
	npm install
	```

2. Set up AWS Credentials.

	```
	aws configure
	```

	Run `cat ~/.aws/credentials` to ensure the credentials are set up properly. Make sure you have the `region` set.

	The output should look similar to:

	```
	[default]
	aws_access_key_id = xxx
	aws_secret_access_key = xxx
	region = us-east-1
	```

	For help, see: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

3. Deploy the stack with serverless.

	```
	serverless deploy
	```

	**NOTE**  If you're using mutliple profiles and not using the `default` profile, you need to create a `.env` file and set `AWS_PROFILE=xyz` where `xyz` is the name of your profile. Run `pipenv shell` to activate virtualenv; this will automatically load the `.env` file too. Now, you can run `serverless deploy` and it will use the proper AWS credentials.

	You can also set `--aws-profile PROFILE` to each serverless command. For help, see: https://serverless.com/framework/docs/providers/aws/guide/credentials/

## Checking Logs

```
serverless logs --function cron --tail
```

## Running locally

```
pipenv shell # activate python virtualenv
serverless invoke local --function cron
```

## Deleting everything

```
serverless remove
```

## Export Data

### Export Single Date

This query exports data from "2018-04-24".

```
aws dynamodb query --table-name onondaga-e911 --key-condition-expression "#d = :date" --expression-attribute-values '{":date": {"S":"2018-04-24"}}' --expression-attribute-names '{"#d":"date"}' > items.json
```

### Export All Data

Please note that the database is provisioned with 1 read capacity unit (RCU). You may want to increase this if you are exporting the entire database.

To summarize, 1 RCU means 2 eventually consistent items read per second. Let's say you're downloading 1 item per minute for the entire year. That's 525,600 items.

At 1 RCU (2 eventually consistent reads per second), 525600 / 2 = 262800 seconds = 73 hours. Obviously, this is prohibitively slow.

If you up the RCU to 50000 (10k eventually consistent reads per second), it will now perform in 525600 / 10000 = 52.56 seconds.

Cost is $0.00013 per RCU per hour (~$0.09 per month) where 1 RCU provides up to 7,200 reads per hour.

**If you set the RCU to 5000, be sure to set it back to 1 within the hour! If you paid for a full month of 5000 RCU, your bill could easily hit $475 for the month!** For just 1 hour at 5000 RCU, you only pay $0.65.

For help, see:
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ProvisionedThroughput.html
- https://aws.amazon.com/dynamodb/faqs/#What_is_a_readwrite_capacity_unit

```
aws dynamodb scan --table-name onondaga-e911 --output json > items.json
```

### Check Read/Write Capacity Units

```
aws dynamodb describe-table --table-name onondaga-e911
```

Check:

```
        "ProvisionedThroughput": {
            "NumberOfDecreasesToday": 0,
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 1
        },
```


### Increase Read Capacity Units

```
aws dynamodb update-table --table-name onondaga-e911 --provisioned-throughput ReadCapacityUnits=10
```
