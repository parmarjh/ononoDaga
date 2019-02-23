import io
import os
import json
import boto3
import arrow
import hashlib
import decimal
import logging
import requests
from bs4 import BeautifulSoup
from boto3.dynamodb.conditions import Key, Attr
import botocore

dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')

SCRAPE_PAGE = os.getenv('SCRAPE_PAGE')
IS_LOCAL = os.getenv('IS_LOCAL')
MAIN_URL = "https://911events.ongov.net/CADInet/app/events.jsp"
MAX_PAGES = 5

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

hashable_keys = [
    'agency', 'category', 'category_details',
    'addr_pre', 'addr_name', 'addr_type', 'addr_suffix', 'addr_place',
    'municipality', 'cross_street1', 'cross_street2',]

def parse_and_save(soup):

    print(soup.select("title")[0].text)
    if not soup.select(r"#form1\:tableEx1\:statistics1"):
        current_page = 1
    else:
        current_page = soup.select(r"#form1\:tableEx1\:statistics1 span")[0].text.split(' ')[1]
    print("current_page", current_page)
    last_update = soup.select("#cdate")[0].text
    print("last_update", last_update)

    for i, row_el in enumerate(soup.select('.dataTableEx > tbody > tr')):

        inserted_timestamp = arrow.utcnow().to("US/Eastern")

        row = {
            "agency": row_el.select('td')[0].text.strip(),
            "category": row_el.select('td')[2].select("span")[0].text.strip(),
            "category_details": row_el.select('td')[2].select("span")[1].text.strip() if len(row_el.select('td')[2].select("span")) > 1 else "",
            "addr_pre": row_el.select('td')[3].select("span")[0].text.strip(), # edirpre1
            "addr_name": row_el.select('td')[3].select("span")[1].text.strip(), # efeatyp1
            "addr_type": row_el.select('td')[3].select("span")[2].text.strip(), # efeanme1
            "addr_suffix": row_el.select('td')[3].select("span")[3].text.strip(),# edirsuf1
            "addr_place": row_el.select('td')[3].select("span")[4].text.strip(), # ecompl1
            "municipality": row_el.select('td')[4].text.strip(), # mun2
            "cross_street1": row_el.select('td')[5].select('[id$=xstreet11]')[0].text,
            "cross_street2": row_el.select('td')[5].select('[id$=xstreet21]')[0].text,
            "inserted_timestamp": inserted_timestamp.isoformat(),
            "inserted_date": inserted_timestamp.date().isoformat(),
        }

        # convert empty string to null because dynamodb doesn't support it yet
        # https://github.com/aws/aws-sdk-java/issues/1189
        row = {k:v if v is not '' else None for k,v in row.items()}

        hasher = hashlib.sha1()
        string_to_hash = ' '.join(row[x] for x in hashable_keys if row[x])
        hasher.update(string_to_hash.encode('utf-8'))
        row_hash = row['hash'] = hasher.hexdigest()

        pending = False
        timestamp_str = row_el.select('td')[1].text.strip()
        if timestamp_str == 'Dispatch Pending':
            pending = True
            # WARNING: if event remains pending near midnight (EST),
            # it will create a duplicate event for the next day
            row['id'] = inserted_timestamp.date().isoformat() + "_" + row_hash
        else:
            timestamp = arrow.get(timestamp_str, "MM/DD/YY HH:mm", tzinfo="US/Eastern")
            row['date'] = timestamp.date().isoformat()
            row['timestamp'] = timestamp.isoformat()
            row['id'] = timestamp.isoformat() + "_" + row_hash

        if SCRAPE_PAGE == 'all':
            if pending:
                table = dynamodb.Table(os.environ['PENDING_EVENTS_TABLE'])
            else:
                table = dynamodb.Table(os.environ['ALL_EVENTS_TABLE'])
        else:
            assert not pending
            table = dynamodb.Table(os.environ['CLOSED_EVENTS_TABLE'])

        try:
            ret = table.put_item(Item=row, ConditionExpression='attribute_not_exists(id)')
            print(f"saved {row['id']} to {table.table_name}")
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"skipping {row['id']}, already saved in {table.table_name}")
            else:
                raise

def scrape(event, context):

    url = os.environ['SCRAPE_URL']

    s = requests.Session()

    response = s.get(MAIN_URL)
    response.raise_for_status()

    if "doLink1Action" in url:
        pass # optimization for "All" page, no need to make second request
    else:
        # make second request to switch to correct page after establishing cookies
        response = s.get(url)
        response.raise_for_status()

    if "There are currently no active events for this agency" in response.text:
        print("No events found.")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    if not soup.select(r"#form1\:tableEx1\:statistics1"):
        num_pages = 1
    else:
        num_pages = int(soup.select(r"#form1\:tableEx1\:statistics1 span")[0].text.split(' ')[-1])
    print("num_pages", num_pages)
    parse_and_save(soup)

    for page in range(1, min(MAX_PAGES, num_pages)): # they internally use zero indexed page numbers
        response = s.post(MAIN_URL, data={"form1": "form1", r"form1\:tableEx1\:web1__pagerWeb": page})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        parse_and_save(soup)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def archive(event, context):
    bucket = s3.Bucket(os.environ['S3_BUCKET'])
    prefix = os.environ['S3_PREFIX']

    query_key = 'date'
    if 'pending' in prefix:
        query_key = 'inserted_date'

    for days_ago in range(0,2+1): # today, yesterday, two days ago
        date = arrow.utcnow().to('US/Eastern').shift(days=-days_ago).date().isoformat()
        print(f"archiving data for {date}")
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        response = table.query(KeyConditionExpression=Key(query_key).eq(date))
        items = response['Items']
        if len(items) == 0:
            print("no items found in dynamo table")
            continue

        if 'pending' in prefix:
            items.sort(key=lambda x: x['inserted_timestamp'])

        key = f"{prefix}{date}.json"
        with io.StringIO() as f:
            for item in items:
                f.write(json.dumps(item, cls=DecimalEncoder) + "\n")
            f.seek(0)
            body = f.read()
        ret = bucket.put_object(Key=key, Body=body, Metadata={
            'ContentType': 'application/json',
            'Count': str(response['Count']),
            'ScannedCount': str(response['ScannedCount']),
            'ResponseMetadata': json.dumps(response['ResponseMetadata'])
            })
        print(ret)

# https://serverless.com/framework/docs/providers/aws/events/apigateway/#request-parameters
# def list_events(event, context):
#     table = dynamodb.Table(os.environ['ALL_EVENTS_TABLE'])

#     # fetch all todos from the database
#     result = table.scan()

#     # create a response
#     response = {
#         "statusCode": 200,
#         "body": json.dumps(result['Items'], cls=DecimalEncoder)
#     }

#     return response
