# onondaga-e911

Scrape Onondaga county's computer aided dispatch (CAD) E911 events: http://wowbn.ongov.net/CADInet/app/events.jsp

![](https://i.imgur.com/Ht2tH4u.png)

## Quickstart

1. Install dependencies.
	
	```
	brew install jq python node
	pip3 install awscli pipenv
	npm install -g serverless
	pipenv install
	npm install
	```

2. Set up AWS.

	- Create an AWS account: https://portal.aws.amazon.com/billing/signup
	- Get the root credentials for your account and keep them in a safe place: https://console.aws.amazon.com/iam/home?#security_credential
	- Add these credentials to the aws command line. Run this command and follow the steps:

		```
		aws configure
		```

		- If you don't know what region to choose, set it to `us-east-1`.
		- If you already have a separate AWS account setup append ` --profile <profile>` to `aws configure`.

		For additional help, see: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

		⚠️ It's not best practice to directly use the root credentials. You ideally want to create an IAM user with just the permissions it needs. This is out of scope for this README. ⚠️

3. Create `.env` file.

	```
	touch .env
	```

	If you are using the `default` aws profile, just leave the file blank. Otherwise, set: `AWS_PROFILE=xyz` where `xyz` is the name of your profile.

4. Deploy the stack with serverless.

	```
	pipenv run serverless deploy -v
	```

	Prefixing with `pipenv run` loads the environment variables that we just set in the `.env` file and then runs the command `serverless deploy`.

	Alternatively, the command `pipenv shell` loads your environment variables in a subshell after which you can just run `serverless deploy`:

	```
	pipenv shell
	serverless deploy -v
	```

	To deploy to production add `--stage prod` to the deploy command: `pipenv run serverless deploy -v --stage prod`

## Caveats

- **Unique Ids**: The majority of issues with the data stem from the fact that there is no unique id per row. To fix this, we create a SHA1 hash of all of the text (excluding the timestamp).
	- The primary key (unique identifier) for the `all` and `closed` tables is `{timestamp}_{hash}`. The timestamp for the `pending` table is `{insertion_date}_{hash}`.
	- Keep in mind that the exact same row data (consisting of agency, address, cross streets etc.) can and very likely will happen multiple times so the `hash` by itself is not globally unique. The `timestamp` is not included as part of the `hash` because there is no fixed timestamp for pending events.

- **Immutable Data**: We assume that each row of data is immutable meaning that once it appears on the website it does not change (no change in category, address, etc.). If any data in a row changes, it will be recorded as a new row because the row's `hash` will change. Unfortunately, I don't know how much this assumption actually holds:

	Here is one such case for an item pending dispatch ([May 10 - Pending](https://s3.amazonaws.com/onondaga-e911-dev/index.html#/?type=pending&date=2018-05-10)):

	![](https://i.imgur.com/kHWYCkh.png)

	Here is another case captured in the all (active) page ([May 11 - All](https://s3.amazonaws.com/onondaga-e911-dev/index.html#/?type=all&date=2018-05-11)):
	
	![](https://i.imgur.com/yjHTXki.png)
	
	You'll see that the item inserted at 1:08 AM (with hash `6c45a830b5`) is the "actual" item. It has a corresponding row in the "closed" page with the same hash. The other hash (`719a02a814`) is no where to be found ([May 11 - Closed](https://s3.amazonaws.com/onondaga-e911-dev/index.html#/?type=closed&date=2018-05-11)):
	
	![](https://i.imgur.com/FBuBlNo.png)
	
	Thus, data changes- it will be difficult to figure out with 100% certainity when this happens. Fortunately, one good clue is that it seems the timestamp remains the same when data changes in the all (active) state.

- **Linking Data**: Data for pending/all/closed events is stored in three separate tables. Looking at a combination of the `hash`, `timestamp`, and the `insertion_timestamp` in each table should help map the lifecycle of an event from pending to all (active) to closed. For example, `(the insertion timestamp of the closed table) - (the insertion timestamp of the `all` table)` should give the length of an event.

- **Pending Events**: The primary key of the pending events table is `{insertion_date}_{hash}`. If an event is inserted near midnight (EST) and remains pending until the next day, a duplicate record will be added. Check the insertion timestamp to ensure there are no back to back records with the same `hash` and consecutive insertion dates.

- **Dynamo/S3**: It can be expensive/slow (without some [finagling](./dynamodb.md)) to download the entire database directly off of DynamoDB when it gets larger (in about a year). This is why the daily S3 dumps are available. See the [Export All Data](#export-all-data) section for more details.

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

## Usage

Start `pipenv shell` before starting to run any commands. This will set the environment variables properly.

### Download Data from S3

#### Download Single Date

```
aws s3 cp s3://onondaga-e911-dev/all/2018-05-17.json .
```

#### Download all data for "closed" page

```
aws s3 sync s3://onondaga-e911-dev/closed .
```

#### Download everything

```
aws s3 sync s3://onondaga-e911-dev .
```

### Download Data directly from DynamoDB

This is a bit more complicated because of the cost structure for DynamoDB. See (./docs/dynamodb.md) for more details.

### Check Logs

```
pipenv shell
serverless logs --function scrape_all --tail
serverless logs --function scrape_closed --tail
serverless logs --function archive_all --tail
serverless logs --function archive_closed --tail
serverless logs --function archive_pending --tail
```

### Running locally

```
pipenv shell # activate python virtualenv
serverless invoke local --function scrape_all
serverless invoke local --function scrape_closed
serverless invoke local --function archive_all
serverless invoke local --function archive_closed
serverless invoke local --function archive_pending
```

### Undeploy All

For `dev` stage:

```
aws s3 rm --recursive s3://onondaga-e911-dev # need to delete contents before bucket
serverless remove
```

### Deploy just UI

```
npm run --prefix ui build
serverless s3deploy -v
```
