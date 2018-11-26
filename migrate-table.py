#!/usr/bin/env python3

import sys
import time
import tqdm
import boto3
import botocore

def scan(table, verbose=False):
    response = table.scan()
    if verbose: print(response['ScannedCount'], response['Count'], response['ResponseMetadata'])
    yield from response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        if verbose: print(response['ScannedCount'], response['Count'], response['ResponseMetadata'])
        yield from response['Items']

def bulk_insert(table, rows, estimated_count, verbose=False):
    with table.batch_writer() as batch:
        for row in tqdm.tqdm(rows, total=estimated_count):
            if verbose: print(f'batch inserting {row["id"]}')
            batch.put_item(Item=row)

def update_throughput(table, *, rcus, wcus):
    try:
        return table.update(ProvisionedThroughput={'ReadCapacityUnits': rcus, 'WriteCapacityUnits': wcus})
    except botocore.exceptions.ClientError as e:
        if "The provisioned throughput for the table will not change." in e.response['Error']['Message']:
            pass
        elif "Table IOPS are currently being updated." in e.response['Error']['Message']:
            print(table.provisioned_throughput)
            pass
        else:
            raise

def wait_for_throughput(table, *, rcus, wcus):
    while True:
        table.reload()
        try:
            assert table.provisioned_throughput['ReadCapacityUnits'] == rcus
            assert table.provisioned_throughput['WriteCapacityUnits'] == wcus
            return
        except AssertionError:
            print(f"throughput not updated yet for {table.table_name}. waiting 20 seconds...", file=sys.stderr)
            time.sleep(20)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="""
    ./migrate-table.py --from-profile al --from-table onondaga-e911-all-dev --to-profile syr --to-table onondaga-e911-all-prod
    ./migrate-table.py --from-profile al --from-table onondaga-e911-closed-dev --to-profile syr --to-table onondaga-e911-closed-prod
    ./migrate-table.py --from-profile al --from-table onondaga-e911-pending-dev --to-profile syr --to-table onondaga-e911-pending-prod
    """)
    parser.add_argument('--from-profile', required=True)
    parser.add_argument('--from-table', required=True)
    parser.add_argument('--to-profile', required=True)
    parser.add_argument('--to-table', required=True)
    parser.add_argument('--throughput', default=1000)
    args = parser.parse_args()

    THROUGHPUT = args.throughput
    FROM = {'profile': args.from_profile, 'table': args.from_table}
    TO = {'profile': args.to_profile, 'table': args.to_table}

    y_n = input(f'Migrating from:\n\t{FROM}\nto\n\t{TO}.\nContinue? [y/n]: ')
    if y_n.lower() != 'y':
        print('Exiting', file=sys.stderr)
        sys.exit(1)

    from_table = boto3.Session(profile_name=FROM['profile']) \
                      .resource('dynamodb').Table(FROM['table'])

    to_table = boto3.Session(profile_name=TO['profile']) \
                    .resource('dynamodb').Table(TO['table'])
    
    print(f'Provisioning {from_table.table_name} to {THROUGHPUT} RCUs and {to_table.table_name} to {THROUGHPUT} WCUs')
    update_throughput(from_table, rcus=THROUGHPUT, wcus=1)
    update_throughput(to_table, rcus=1, wcus=THROUGHPUT)

    print('Waiting until throughput has changed')
    wait_for_throughput(from_table, rcus=THROUGHPUT, wcus=1)
    wait_for_throughput(to_table, rcus=1, wcus=THROUGHPUT)

    print('Begin Migration')
    bulk_insert(to_table, scan(from_table), from_table.item_count)

    print(f'Provisioning {from_table.table_name} and {to_table.table_name} back to 1 WCU/RCU')
    update_throughput(from_table, rcus=1, wcus=1)
    update_throughput(to_table, rcus=1, wcus=1)

    print('Waiting until throughput has changed')
    wait_for_throughput(from_table, rcus=1, wcus=1)
    wait_for_throughput(to_table, rcus=1, wcus=1)
