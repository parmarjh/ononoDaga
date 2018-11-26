# onondaga-e911

Scrape Onondaga county's computer aided dispatch (CAD) E911 events: http://wowbn.ongov.net/CADInet/app/events.jsp

![](https://i.imgur.com/Ht2tH4u.png)

## Quickstart

1. Clone repository.

	- change directory (cd) to your projects or development folder

		```
		cd ~/Development
		```

	- clone the repository and cd into the repository folder

		```
		git clone git@github.com:AlJohri/onondaga-e911.git
		cd onondaga-e911
		```

	- Run all commands below from the `onondaga-e911` folder.

2. Install dependencies.

	```
	brew install jq python node awscli pipenv
	pipenv install
	npm install
	```

3. Set up AWS.

	- Create an AWS account: https://portal.aws.amazon.com/billing/signup
	- Get the root credentials for your account and keep them in a safe place: https://console.aws.amazon.com/iam/home?#security_credential
	- Add these credentials to the aws command line. Run this command and follow the steps:

		```
		aws configure
		```

		- If you don't know what region to choose, set it to `us-east-1`.
		- If you already have a separate AWS account setup append ` --profile <profile>` to `aws configure`.

		For additional help, see: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

		⚠️ It's not [best practice](https://docs.aws.amazon.com/general/latest/gr/root-vs-iam.html) to directly use the root credentials. You ideally want to create an IAM user with just the permissions it needs. Please see [docs/iam.md](./docs/iam.md) for instructions on how to do this. ⚠️

4. Create `.env` file.

	```
	touch .env
	```

	If you are using the `default` aws profile, just leave the file blank. Otherwise, open the file and write `AWS_PROFILE=xyz` (where `xyz` is the name of your profile) into the first line of the file and save.

5. Deploy the stack with serverless.

	```
	pipenv run npx serverless deploy -v
	```

	Prefixing with `pipenv run` loads the environment variables that we just set in the `.env` file and then runs the command `npx serverless deploy`.

## Data

I recommend reading the [caveats](./docs/caveats.md) in detail before using this data.

**UI**

_Chrome Only_

https://s3.amazonaws.com/onondaga-e911-prod/index.html

**DynamoDB Tables**

- `onondaga-e911-all-prod`
- `onondaga-e911-closed-prod`
- `onondaga-e911-pending-prod`

**S3 Folders**:

- `s3://onondaga-e911-prod/all/`
- `s3://onondaga-e911-prod/closed/`
- `s3://onondaga-e911-prod/pending/`

## Usage

🚨 Start `pipenv shell` before starting to run ANY of the commands below. This will start a python virtualenv and set the environment variables (`.env`) properly. 🚨

### Download Data from S3

#### Download Single Date

```
aws s3 cp s3://onondaga-e911-prod/all/2018-05-17.json .
```

#### Download all data for "closed" page

```
aws s3 sync s3://onondaga-e911-prod/closed .
```

#### Download everything

```
aws s3 sync s3://onondaga-e911-prod .
```

### Download Data directly from DynamoDB

This is a bit more complicated because of the cost structure for DynamoDB. See [docs/dynamodb.md](./docs/dynamodb.md) for more details.

### Check Logs

```
npx serverless logs --function scrape_all --tail
npx serverless logs --function scrape_closed --tail
npx serverless logs --function archive_all --tail
npx serverless logs --function archive_closed --tail
npx serverless logs --function archive_pending --tail
```

### Running locally

```
npx serverless invoke local --function scrape_all
npx serverless invoke local --function scrape_closed
npx serverless invoke local --function archive_all
npx serverless invoke local --function archive_closed
npx serverless invoke local --function archive_pending
```

## Deploying UI

```
pipenv run npx serverless s3deploy -v
```

<!--

Leaving this commented out to prevent anyone from ever running this.

### Undeploy All

🚨 This will delete the data (dynamo tables and s3 bucket)! 🚨

```
aws s3 rm --recursive s3://onondaga-e911-prod # need to delete contents of bucket before deleting the bucket itself
npx serverless remove -v
```

-->
