import os
import json
import boto3
import arrow
import logging
import requests
import datetime
from bs4 import BeautifulSoup

dynamodb = boto3.resource('dynamodb')

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
