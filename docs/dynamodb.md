# DynamoDB

## Export Single Date from DynamoDB

This command exports data from "2018-05-17".

```
aws dynamodb query --table-name onondaga-e911-all-prod --key-condition-expression "#d = :date" --expression-attribute-values '{":date": {"S":"2018-05-17"}}' --expression-attribute-names '{"#d":"date"}' --return-consumed-capacity TOTAL | jq -f filter.jq
```

## Explore All from DynamoDB

Please note that the database is provisioned with 1 read capacity unit (RCU). You may want to increase this if you are exporting the entire database directly from DynamoDB.

## Read Capacity Units (RCUs)

### Overview

1 RCU = 2 (eventually consistent) reads per second = $0.00013 per RCU per hour (~$0.09 per month)

This assumes items are < 4kb (for this project, all items are much smaller than 4kb).

### Example

Let's say you're scraping 1 item per minute for the entire year. That's 525,600 items for the entire year.

- At 1 RCU (2 reads per second), 525600 / 2 = 262800 seconds = 73 hours. Obviously, this is prohibitively slow.
- At 5000 RCUs (10k reads per second), 525600 / 10000 = 52.56 seconds.

**If you set the RCU to 5000, be sure to set it back to 1 within the hour! If you paid for a full month of 5000 RCU, your bill could easily hit $475 for the month!**

For just 1 hour at 5000 RCU, you only pay $0.65.

For help, see:
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ProvisionedThroughput.html
- https://aws.amazon.com/dynamodb/faqs/#What_is_a_readwrite_capacity_unit

### Check Read/Write Capacity Units

```
aws dynamodb describe-table --table-name onondaga-e911-all-prod
```

Check:

```
"ProvisionedThroughput": {
    "NumberOfDecreasesToday": 0,
    "ReadCapacityUnits": 1,
    "WriteCapacityUnits": 1
},
```

### Change Read Capacity Units

```
aws dynamodb update-table --table-name onondaga-e911-all-prod --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=1
```

### Download All the Data

Once you've adjusted your Read Capacity Units (so the command doesn't run forever)...

```
npx dyno scan us-east-1/onondaga-e911-all-prod | jq -f filter.jq
npx dyno scan us-east-1/onondaga-e911-closed-prod | jq -f filter.jq
```

You can pipe this into a file to save the data. This pipes the output into `onondaga-e911-all-prod.json` and `onondaga-e911-closed-prod.json` respectively.

```
npx dyno scan us-east-1/onondaga-e911-all-prod | jq -Mcf filter.jq > onondaga-e911-all-prod.json
npx dyno scan us-east-1/onondaga-e911-closed-prod | jq -Mcf filter.jq > onondaga-e911-closed-prod.json
```
