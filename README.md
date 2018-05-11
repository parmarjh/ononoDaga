# onondaga-e911

Scrape Onondaga county's computer aided dispatch (CAD) E911 events: http://wowbn.ongov.net/CADInet/app/events.jsp

## Data

- **Dev UI**: https://s3.amazonaws.com/onondaga-e911-dev/index.html
- **Prod UI**: https://s3.amazonaws.com/onondaga-e911-prod/index.html

**DynamoDB Tables**

- `onondaga-e911-all-(dev|prod)`
- `onondaga-e911-closed-(dev|prod)`
- `onondaga-e911-pending-(dev|prod)`

**S3 Folders**:

- `s3://onondaga-e911-(dev|prod)/all/`
- `s3://onondaga-e911-(dev|prod)/closed/`
- `s3://onondaga-e911-(dev|prod)/pending/`

## Caveats

- **Unique Ids**: The majority of issues with the data stem from the fact that there is no unique id per row. To fix this, we create a SHA1 hash of all of the text (excluding the timestamp).
	- The primary key (unique identifier) for the `all` and `closed` tables is `{timestamp}_{hash}`. The timestamp for the `pending` table is `{insertion_date}_{hash}`.
	- Keep in mind that the exact same row data (consisting of agency, address, cross streets etc.) can and very likely will happen multiple times so the `hash` by itself is not globally unique. The `timestamp` is not included as part of the `hash` because there is no fixed timestamp for pending events.

- **Immutable Data**: We assume that each row of data is immutable meaning that once it appears on the website it does not change (no change in category, address, etc.). If any data in a row changes, it will be recorded as a new row because the row's `hash` will change. Unfortunately, I don't know how much this assumption actually holds:

	Here is one such case for an item pending dispatch:

	![](https://i.imgur.com/kHWYCkh.png)
	
	Here is another case captured in the all (active) page:
	
	![](https://i.imgur.com/yjHTXki.png)
	
	You'll see that the item inserted at 1:08 AM (with hash `6c45a830b5`) is the "actual" item. It has a corresponding row in the "closed" page with the same hash. The other hash (`719a02a814`) is no where to be found:
	
	![](https://i.imgur.com/FBuBlNo.png)
	
	Thus, data changes- it will be difficult to figure out with 100% certainity when this happens. Fortunately, one good clue is that it seems the timestamp remains the same when data changes in the all (active) state.

- **Linking Data**: Data for pending/all/closed events is stored in three separate tables. Looking at a combination of the `hash`, `timestamp`, and the `insertion_timestamp` in each table should help map the lifecycle of an event from pending to all (active) to closed. For example, `(the insertion timestamp of the closed table) - (the insertion timestamp of the `all` table)` should give the length of an event.

- **Pending Events**: The primary key of the pending events table is `{insertion_date}_{hash}`. If an event is inserted near midnight (EST) and remains pending until the next day, a duplicate record will be added. Check the insertion timestamp to ensure there are no back to back records with the same `hash` and consecutive insertion dates.

- **Dynamo/S3**: It can be expensive/slow (without some [finagling](./dynamodb.md)) to download the entire database directly off of DynamoDB when it gets larger (in about a year). This is why the daily S3 dumps are available. See the [Export All Data](#export-all-data) section for more details.

## Quickstart

1. Install dependencies.

	Must have node and python3.6 installed.

	```
	brew install jq
	pip3 install awscli
	pip3 install pipenv
	pipenv install
	npm install -g serverless
	npm install -g @mapbox/dyno
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
	serverless deploy -v
	npm run --prefix ui build
	serverless s3deploy -v
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
serverless invoke local --function scrape_closed
serverless invoke local --function archive_all
serverless invoke local --function archive_closed
serverless invoke local --function archive_pending
```

## Deleting everything

For `dev` stage:

```
aws s3 rm --recursive s3://onondaga-e911-dev # need to delete contents before bucket
serverless remove
```

## Export

### Export Single Date

This command exports data from "2018-05-09".

```
aws dynamodb query --table-name onondaga-e911-all-dev --key-condition-expression "#d = :date" --expression-attribute-values '{":date": {"S":"2018-05-09"}}' --expression-attribute-names '{"#d":"date"}' --return-consumed-capacity TOTAL | jq -f filter.jq
```

### Export All Data

## S3

For large data dumps, use S3. The latest three (today, yesterday, day before) files are updated hourly.

This command will download the entire bucket:

```
aws s3 sync s3://onondaga-e911-dev .
```

This command will just download the `all` folder:

```
aws s3 sync s3://onondaga-e911-dev/all .
```

## DynamoDB

Please note that the database is provisioned with 1 read capacity unit (RCU). You may want to increase this if you are exporting the entire database directly from DynamoDB. Check [dynamo.md](./dynamo.md) for more details.

```
dyno scan us-east-1/onondaga-e911-all-dev | jq -f filter.jq
dyno scan us-east-1/onondaga-e911-closed-dev | jq -f filter.jq
```

You can pipe this into a file to save the data. This pipes the output into `onondaga-e911-all-dev.json` and `onondaga-e911-closed-dev.json` respectively.

```
dyno scan us-east-1/onondaga-e911-all-dev | jq -Mcf filter.jq > onondaga-e911-all-dev.json
dyno scan us-east-1/onondaga-e911-closed-dev | jq -Mcf filter.jq > onondaga-e911-closed-dev.json
```
