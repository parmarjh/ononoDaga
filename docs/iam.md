# iam

1. Go to the IAM page (https://console.aws.amazon.com/iam/home?region=us-east-1#/home) and click "Add User".

2. Set user name to whatever you want and choose **both** "Programmatic access" and "AWS Management Console access" for "Access type".

3. Choose "Attach existing policies directly". Give the following permissions:

    - AmazonDynamoDBFullAccess
    - AWSLambdaFullAccess
    - AmazonS3FullAccess
    - CloudWatchFullAccess
    - IAMFullAccess

4. You also need to add permission for full access to CloudFormation. Unfortunately this isn't a managed policy that we can just choose from the list so you must use this policy document:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStackResource",
                "cloudformation:GetTemplate",
                "cloudformation:ValidateTemplate",
                "cloudformation:UpdateStack",
                "cloudformation:ListStacks"
            ],
            "Resource": "*"
        }
    ]
}
```

5. Click next and accept the defaults for the remaining steps.

6. Run `aws configure` and use the programmatic access keys you recieved above.
