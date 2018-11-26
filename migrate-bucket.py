#!/usr/bin/env python3

import sys
import time
import tqdm
import boto3
import botocore

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="""
    ./migrate-bucket.py --from-profile al --from-bucket onondaga-e911-dev --to-profile syr --to-bucket onondaga-e911-prod
    """)
    parser.add_argument('--from-profile', required=True)
    parser.add_argument('--from-bucket', required=True)
    parser.add_argument('--to-profile', required=True)
    parser.add_argument('--to-bucket', required=True)
    parser.add_argument('--throughput', default=1000)
    args = parser.parse_args()

    THROUGHPUT = args.throughput
    FROM = {'profile': args.from_profile, 'bucket': args.from_bucket}
    TO = {'profile': args.to_profile, 'bucket': args.to_bucket}

    y_n = input(f'Migrating from:\n\t{FROM}\nto\n\t{TO}.\nContinue? [y/n]: ')
    if y_n.lower() != 'y':
        print('Exiting', file=sys.stderr)
        sys.exit(1)

    from_bucket = boto3.Session(profile_name=FROM['profile']) \
                       .resource('s3').Bucket(FROM['bucket'])

    to_bucket = boto3.Session(profile_name=TO['profile']) \
                    .resource('s3').Bucket(TO['bucket'])
    
    for obj in from_bucket.objects.all():
        key = obj.key
        obj = obj.get()
        body = obj['Body'].read()
        new_obj = to_bucket.put_object(Key=key, Body=body, Metadata=obj['Metadata'])
        print(new_obj)
