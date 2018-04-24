import os
import json
import boto3
import arrow
import logging
import requests
import datetime
from bs4 import BeautifulSoup

dynamodb = boto3.resource('dynamodb')

ALL_URL = "http://wowbn.ongov.net/CADInet/app/_rlvid.jsp?_rap=pc_Cad911Toweb.doLink1Action&_rvip=/events.jsp"
CLOSED_EVENTS_URL = "http://wowbn.ongov.net/CADInet/app/_rlvid.jsp?_rap=pc_Cad911Toweb.doLink7Action&_rvip=/events.jsp"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def run(event, context):

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    current_time = datetime.datetime.now().time()
    name = context.function_name
    logger.info("Your cron function " + name + " ran at " + str(current_time))

    response = requests.get(ALL_URL)

    if "There are currently no active events for this agency" in response.text:
        print("No events found.")
        return []

    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    last_update = soup.select("#cdate")[0].text
    print(last_update)

    headers = [
        "agency",
        "timestamp",
        "category",
        "address",
        "township",
        "cross_streets"
    ]

    rows = []
    for i, row_el in enumerate(soup.select('.dataTableEx > tbody > tr')):
        raw_data = tuple(x.text.strip() for x in row_el.select('td'))
        assert len(raw_data) == 6
        hashed = hash(raw_data)
        # convert empty string to null because dynamodb doesn't support it yet
        # https://github.com/aws/aws-sdk-java/issues/1189
        row = {headers[j]: x if x != "" else None for j, x in enumerate(raw_data)}
        timestamp = arrow.get(row['timestamp'], "MM/DD/YY HH:mm", tzinfo="US/Eastern")
        row['timestamp'] = timestamp.isoformat()
        row['date'] = timestamp.date().isoformat()
        row['hash'] = hashed
        row['timestamp_hash'] = row['timestamp'] + "_" + str(row['hash'])
        rows.append(row)
        print(i, row)
        ret = table.put_item(Item=row)
        print(ret)

    return rows
