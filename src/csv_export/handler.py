import os
import re
from datetime import date, timedelta

import boto3

TIMESTREAM_DB_NAME = os.environ["TIMESTREAM_DB_NAME"]
USER_RESULT_TABLE = os.environ["USER_RESULT_TABLE"]
BASIC_RESULT_TABLE = os.environ["BASIC_RESULT_TABLE"]
EXPORT_BUCKET = os.environ["EXPORT_BUCKET"]
client = boto3.client("timestream-query")


def origin(_, __):
    yesterday = date.today() - timedelta(days=1)

    for table in (USER_RESULT_TABLE, BASIC_RESULT_TABLE):
        query = f"""
        UNLOAD (
            SELECT *
            FROM "{TIMESTREAM_DB_NAME}"."{table}"
            WHERE time BETWEEN bin(now(), 1d) - 1d AND bin(now(), 1d)
        ) TO 's3://{EXPORT_BUCKET}/origin/{yesterday.strftime('%Y-%m-%d')}/{table}'
        """
        try:
            client.query(QueryString=query)
        except Exception as e:
            print("query = " + re.sub("\s+", " ", query))
            raise e
    return None
