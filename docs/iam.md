# iam

1. Go to the IAM page (https://console.aws.amazon.com/iam/home?region=us-east-1#/home) and click "Add User".

2. Set user name to whatever you want and choose both "Programmatic access" and "AWS Management Console access" for "Access type".

3. Choose "Attach existing policies directly". Give the following permissions:

    - AmazonDynamoDBFullAccess
    - AWSLambdaFullAccess
    - AmazonS3FullAccess
    - CloudWatchFullAccess

4. Run `aws configure` and use the programmatic access keys you recieved above.
