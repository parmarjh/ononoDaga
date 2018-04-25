# onondaga-e911

Scrape Onondaga county's computer aided dispatch (CAD) E911 events: http://wowbn.ongov.net/CADInet/app/events.jsp

## Quickstart

1. Install dependencies.

	Must have node and python3.6 installed.

	```
	pip3 install awscli
	pip3 install pipenv
	pipenv install
	npm install -g serverless
	npm install -g dynamodump
	npm install
	```

2. Set up AWS Credentials.

	You have two options for AWS Credentials: root user (easy, less secure) or creating IAM roles (slightly more work, more secure).

	To get the root AWS credentials of your account, go here: https://console.aws.amazon.com/iam/home?#security_credential

	To instead create a specific IAM user, go here: https://console.aws.amazon.com/iam/home?#/users You will need to allow the user to create lambdas, dynamodb tables, and log groups.

	Once you have the aws access key id and aws secret access key, this command below will help you set up the `default` profile for AWS:

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

3. Create `.env` file.

	```
	touch .env
	```

	If you are using the `default` aws role, just leave the file blank. Otherwise, set: `AWS_PROFILE=xyz` where `xyz` is the name of your profile.

4. Deploy the stack with serverless.

	`pipenv shell` will activate a virtualenv and load your environment variables. `serverless deploy` will create the stack on AWS.

	```
	pipenv shell
	serverless deploy
	```

	To deploy to production add `--stage prod` to the deploy command.

## Checking Logs

Function names are `scrape_all` or `scrape_closed`.

```
serverless logs --function scrape_all --tail
```

## Running locally

```
pipenv shell # activate python virtualenv
serverless invoke local --function scrape_all
```

## Deleting everything

```
serverless remove
```

## Export Data

The names of tables are `onondaga-e911-(all|closed)-(dev|prod)`. For example `onondaga-e911-all-dev`.

### Export Single Date

This command exports data from "2018-04-24" into a file named `events.json`.

```
aws dynamodb query --table-name onondaga-e911-all-dev --key-condition-expression "#d = :date" --expression-attribute-values '{":date": {"S":"2018-04-24"}}' --expression-attribute-names '{"#d":"date"}' > events.json
```

### Export All Data

Please note that the database is provisioned with 1 read capacity unit (RCU). You may want to increase this if you are exporting the entire database. Check [dynamo.md](./dynamo.md) for more details.

```
dynamodump export-data --table onondaga-e911-all-dev --region us-east-1
```
