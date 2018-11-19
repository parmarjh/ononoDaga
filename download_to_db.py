#!/usr/bin/env python3

import json
import argparse
import datetime
import sqlite3
import concurrent.futures
import urllib.request

def make_url(page, date):
    return "https://s3.amazonaws.com/onondaga-e911-dev/%s/%s.json" % (page, date)

def get_date_range(start, end):
    delta = end - start
    for i in range(delta.days + 1):
        yield start + datetime.timedelta(i)

def load_url(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        return conn.read().decode('utf-8')

def download(urls):
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(load_url, url, 60): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                print('%s generated an exception: %s' % (url, exc))
            else:
                print('%s downloaded' % url)
                rows += [json.loads(line) for line in data.splitlines()]
    return rows

def setup_tables():

    global conn, cur

    columns = """
        id TEXT PRIMARY KEY,
        agency TEXT,
        category TEXT,
        category_details TEXT,
        addr_pre TEXT,
        addr_name TEXT,
        addr_type TEXT,
        addr_suffix TEXT,
        addr_place TEXT,
        municipality TEXT,
        cross_street1 TEXT,
        cross_street2 TEXT,
        inserted_timestamp TEXT,
        inserted_date TEXT
    """.strip()

    sql = """
    CREATE TABLE IF NOT EXISTS all_page (
        %s,
        date TEXT,
        timestamp TEXT
    )
    """ % columns
    cur.execute(sql)

    sql = """
    CREATE TABLE IF NOT EXISTS closed_page (
        %s,
        date TEXT,
        timestamp TEXT
    )
    """ % columns
    cur.execute(sql)

    sql = "CREATE TABLE IF NOT EXISTS pending_page (%s)" % columns
    cur.execute(sql)

def insert_row(row, table, verbose=False):

    global conn, cur

    columns = [
        'id', 'agency', 'category', 'category_details',
        'addr_pre', 'addr_name', 'addr_type', 'addr_suffix', 'addr_place',
        'municipality', 'cross_street1', 'cross_street2',
        'inserted_timestamp', 'inserted_date'
    ]

    if table in ['all_page', 'closed_page']:
        columns += ['date', 'timestamp']

    values = ('?,' * len(columns)).rstrip(',')

    sql = "INSERT INTO %s(%s) VALUES(%s)" % (table, ','.join(columns), values)
    cur = conn.cursor()
    try:
        cur.execute(sql, [row[c] for c in columns])
    except sqlite3.IntegrityError:
        conn.rollback()
        if verbose: print('already exists', row["id"])
    else:
        conn.commit()
        if verbose: print('inserted', row["id"])

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('start', help='start date')
    parser.add_argument('end', help='end date')
    parser.add_argument('--page',
        choices=('all', 'closed', 'pending'),
        default='all',
        metavar='page', help='Choose between "all", "closed", and "pending". Default is "all".')
    parser.add_argument('--db',
        default='onondaga.db',
        help='Database where data will be downloaded into.')
    parser.add_argument('--verbose', action='store_true', default=False)
    args = parser.parse_args()

    start = datetime.datetime.strptime(args.start, r'%Y-%m-%d').date()
    end = datetime.datetime.strptime(args.end, r'%Y-%m-%d').date()
    urls = [make_url(args.page, date) for date in get_date_range(start, end)]
    rows = download(urls)
    print('finished downloading %s rows from %s dates' % (len(rows), len(urls)))

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    setup_tables()
    table = args.page + "_page"
    for row in rows:
        insert_row(row, table, args.verbose)
    print('finished inserting %s rows into table %s of db %s' % (len(rows), table, args.db))
