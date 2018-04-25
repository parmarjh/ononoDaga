import io
import os
import json
import boto3
import arrow
import decimal
import logging
import requests
from bs4 import BeautifulSoup
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')

INIT_URL = "http://wowbn.ongov.net/CADInet/app/events.jsp"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def scrape(event, context):

    url = os.environ['SCRAPE_URL']
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    
    s = requests.Session()

    response = s.get(INIT_URL)
    response.raise_for_status()

    if "doLink1Action" in url:
        pass # optimization for "All" page, no need to make second request
    else:
        # make second request after establishing cookies
        response = s.get(url)
        response.raise_for_status()

    if "There are currently no active events for this agency" in response.text:
        print("No events found.")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    last_update = soup.select("#cdate")[0].text
    print(last_update)

    headers = [
        "agency",
        "timestamp",
        "category",
        "address_pre", 
        "address_name", # efeanme1
        "address_type", 
        "address_suffix", # edirsuf1
        "address_place", # ecompl1
        "township",
        "cross_streets"
    ]

    rows = []
    for i, row_el in enumerate(soup.select('.dataTableEx > tbody > tr')):
        row = {
            "agency": row_el.select('td')[0].text.strip(),
            "timestamp": row_el.select('td')[1].text.strip(),
            "category": row_el.select('td')[2].text.strip(),
            "address_pre": row_el.select('td')[3].select("span")[0].text.strip(), # edirpre1
            "address_name": row_el.select('td')[3].select("span")[1].text.strip(), # efeatyp1
            "address_type": row_el.select('td')[3].select("span")[2].text.strip(), # efeanme1
            "address_suffix": row_el.select('td')[3].select("span")[3].text.strip(),# edirsuf1
            "address_place": row_el.select('td')[3].select("span")[4].text.strip(), # ecompl1
            "municipality": row_el.select('td')[4].text.strip(), # mun2
            "cross_street1": row_el.select('td')[5].select('[id$=xstreet11]')[0].text,
            "cross_street2": row_el.select('td')[5].select('[id$=xstreet21]')[0].text,
        }
        hashed = hash(tuple(row.values()))
        # convert empty string to null because dynamodb doesn't support it yet
        # https://github.com/aws/aws-sdk-java/issues/1189
        row = {k:v if v is not '' else None for k,v in row.items()}
        timestamp = arrow.get(row['timestamp'], "MM/DD/YY HH:mm", tzinfo="US/Eastern")
        row['timestamp'] = timestamp.isoformat()
        row['date'] = timestamp.date().isoformat()
        row['hash'] = hashed
        row['timestamp_hash'] = row['timestamp'] + "_" + str(row['hash'])
        rows.append(row)
        print(i, row)
        ret = table.put_item(Item=row)
        # print(ret)

    return rows

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
    date = arrow.utcnow().to('US/Eastern').shift(days=-2).date().isoformat()
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    response = table.query(KeyConditionExpression=Key('date').eq(date))
    items = response['Items']
    if len(items) == 0:
        return
    key = f"{prefix}{date}.json"
    with io.StringIO() as f:
        for item in items:
            f.write(json.dumps(item, cls=DecimalEncoder) + "\n")
        f.seek(0)
        body = f.read()
    ret = bucket.put_object(Key=key, Body=body, Metadata={
        'Count': str(response['Count']),
        'ScannedCount': str(response['ScannedCount']),
        'ResponseMetadata': json.dumps(response['ResponseMetadata'])
        })
    return str(ret)
