#!/usr/bin/env python3

import json
import argparse
import datetime
import itertools
import sqlite3
import concurrent.futures
import urllib.request

def grouper(iterable, n):
    # https://docs.python.org/3.7/library/itertools.html#itertools-recipes
    "Collect data into fixed-length chunks or blocks"
    args = [iter(iterable)] * n
    for batch in itertools.zip_longest(*args, fillvalue=None):
        yield filter(None.__ne__, batch)

def make_url(page, date):
    return "https://s3.amazonaws.com/onondaga-e911-prod/%s/%s.json" % (page, date)

def get_date_range(start, end):
    delta = end - start
    for i in range(delta.days + 1):
        yield start + datetime.timedelta(i)

def load_url(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        return conn.read().decode('utf-8')

def download(urls, verbose=False):
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
                if verbose: print('%s downloaded' % url)
                rows += [json.loads(line) for line in data.splitlines()]
    return rows

def setup_tables(conn):

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
    conn.execute(sql)

    sql = """
    CREATE TABLE IF NOT EXISTS closed_page (
        %s,
        date TEXT,
        timestamp TEXT
    )
    """ % columns
    conn.execute(sql)

    sql = "CREATE TABLE IF NOT EXISTS pending_page (%s)" % columns
    conn.execute(sql)

def insert_rows(conn, rows, table, verbose=False):

    columns = [
        'id', 'agency', 'category', 'category_details',
        'addr_pre', 'addr_name', 'addr_type', 'addr_suffix', 'addr_place',
        'municipality', 'cross_street1', 'cross_street2',
        'inserted_timestamp', 'inserted_date'
    ]

    if table in ['all_page', 'closed_page']:
        columns += ['date', 'timestamp']

    if verbose:
        print('inserting', row["id"])

    columns_str = ','.join(columns)
    question_marks = ('?,' * len(columns)).rstrip(',')
    sql = "INSERT OR IGNORE INTO {table}({columns_str}) VALUES({question_marks})".format(
        table=table,
        columns_str=columns_str,
        question_marks=question_marks)
    conn.executemany(sql, [[row[c] for c in columns] for row in rows])
    conn.commit()

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
    parser.add_argument('--verbose', action='store_true', default=False,
        help='')
    parser.add_argument('--batch-size', type=int, default=2000,
        help='Number of rows inserted into sqlite database at a time.')
    args = parser.parse_args()

    start = datetime.datetime.strptime(args.start, r'%Y-%m-%d').date()
    end = datetime.datetime.strptime(args.end, r'%Y-%m-%d').date()
    urls = [make_url(args.page, date) for date in get_date_range(start, end)]
    print('downloading data between %s and %s (%s days)' % (start, end, len(urls)))
    rows = download(urls)
    print('finished downloading %s rows from %s dates' % (len(rows), len(urls)))

    conn = sqlite3.connect(args.db)
    if args.verbose:
        conn.set_trace_callback(print)
    setup_tables(conn)
    table = args.page + "_page"
    for batch in grouper(rows, args.batch_size):
        insert_rows(conn, batch, table, args.verbose)
    print('finished inserting %s rows into table %s of db %s' % (len(rows), table, args.db))
