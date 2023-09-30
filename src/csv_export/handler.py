import csv
import json
import os
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path

import boto3
from google.cloud import storage

TIMESTREAM_DB_NAME = os.environ["TIMESTREAM_DB_NAME"]
ORIGIN_TABLE = os.environ["ORIGIN_TABLE"]
AGGREGATION_RESULT_TABLE = os.environ["AGGREGATION_RESULT_TABLE"]
EXPORT_S3_BUCKET = os.environ["EXPORT_S3_BUCKET"]
EXPORT_GCS_BUCKET = os.environ["EXPORT_GCS_BUCKET"]
client = boto3.client("timestream-query")


def origin(_, __):
    yesterday = date.today() - timedelta(days=1)

    query = f"""
    UNLOAD (
        SELECT *
        FROM "{TIMESTREAM_DB_NAME}"."{ORIGIN_TABLE}"
        WHERE time BETWEEN bin(now(), 1d) - 1d AND bin(now(), 1d)
    ) TO 's3://{EXPORT_S3_BUCKET}/origin/{yesterday.strftime('%Y-%m-%d')}/{ORIGIN_TABLE}'
    """
    try:
        client.query(QueryString=query)
    except Exception as e:
        print("query = " + re.sub("\s+", " ", query))
        raise e
    return None


def aggregate(_, __):
    gcs = storage.Client()
    bucket = gcs.bucket(EXPORT_GCS_BUCKET)
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    with open(Path(__file__).with_name("pokemon_names.json"), "rt") as fr:
        pokemon_names = json.load(fr)

    with tempfile.TemporaryDirectory() as tmpdirname:
        query = f"""
        SELECT
            pokemon,
            date(time) AS date,
            first_picked,
            first_picked_win,
            second_picked,
            second_picked_win,
            first_banned,
            first_banned_win,
            second_banned,
            second_banned_win,
            banned,
            match_total
        FROM "{TIMESTREAM_DB_NAME}"."{AGGREGATION_RESULT_TABLE}"
        WHERE
            time = bin(now(), 1d) - 1d
            AND namespace = 'default'
            AND measure_name = 'aggregate_by_pokemon'
        ORDER BY first_picked + second_picked + banned DESC
        """
        response = client.query(QueryString=query)

        tmpfile = os.path.join(tmpdirname, "tmp.csv")
        with open(tmpfile, "wt") as fw:
            writer = csv.writer(fw)
            writer.writerow(
                [
                    "ポケモン",
                    "英語名",
                    "日付",
                    "先攻ピック数",
                    "先攻ピック勝利数",
                    "後攻ピック数",
                    "後攻ピック勝利数",
                    "先攻使用禁止数",
                    "先攻使用禁止勝利数",
                    "後攻使用禁止数",
                    "後攻使用禁止勝利数",
                    "使用禁止数",
                    "対戦総数",
                ]
            )
            for row in response["Rows"]:
                record = [data.get("ScalarValue") for data in row["Data"]]
                record.insert(0, pokemon_names[record[0]])
                writer.writerow(record)
        blob = bucket.blob(f"default/aggregate_by_pokemon/aggregate_by_pokemon_{yesterday}.csv")
        blob.upload_from_filename(tmpfile)
        print(f"aggregate_by_pokemon_{yesterday}.csv completed.")

        query = f"""
        SELECT
            pokemon,
            move1,
            move2,
            date(time) AS date,
            first_picked,
            first_picked_win,
            second_picked,
            second_picked_win,
            match_total
        FROM "{TIMESTREAM_DB_NAME}"."{AGGREGATION_RESULT_TABLE}"
        WHERE
            time = bin(now(), 1d) - 1d
            AND namespace = 'default'
            AND measure_name = 'aggregate_by_pokemon_move'
        ORDER BY first_picked + second_picked DESC
        """
        response = client.query(QueryString=query)

        tmpfile = os.path.join(tmpdirname, "tmp.csv")
        with open(tmpfile, "wt") as fw:
            writer = csv.writer(fw)
            writer.writerow(
                [
                    "ポケモン",
                    "英語名",
                    "技1",
                    "技2",
                    "日付",
                    "先攻ピック数",
                    "先攻ピック勝利数",
                    "後攻ピック数",
                    "後攻ピック勝利数",
                    "対戦総数",
                ]
            )
            for row in response["Rows"]:
                record = [data.get("ScalarValue") for data in row["Data"]]
                record.insert(0, pokemon_names[record[0]])
                writer.writerow(record)
        blob = bucket.blob(f"default/aggregate_by_pokemon_move/aggregate_by_pokemon_move_{yesterday}.csv")
        blob.upload_from_filename(tmpfile)
        print(f"aggregate_by_pokemon_move_{yesterday}.csv completed.")
