# aws

some commands to help delete stuff when serverless messes up

```
aws dynamodb list-tables
aws dynamodb list-tables | jq -r '.TableNames[]' | xargs -tL 1 aws dynamodb delete-table --table-name
```

```
aws cloudformation list-stacks | jq -r '.StackSummaries[].StackId' | xargs -tL 1 aws cloudformation delete-stack --stack-name
```

```
aws s3 rm --recursive s3://onondaga-e911-dev
aws s3api delete-bucket --bucket onondaga-e911-dev
```
