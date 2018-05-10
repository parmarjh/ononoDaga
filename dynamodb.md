# DynamoDB

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
aws dynamodb describe-table --table-name onondaga-e911-all-dev
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
aws dynamodb update-table --table-name onondaga-e911-all-dev --provisioned-throughput ReadCapacityUnits=10
```
