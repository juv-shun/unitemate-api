import csv
import json
import os
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path

import boto3

TIMESTREAM_DB_NAME = os.environ["TIMESTREAM_DB_NAME"]
USER_RESULT_TABLE = os.environ["USER_RESULT_TABLE"]
POKEMON_AGGREGATION_TABLE = os.environ["POKEMON_AGGREGATION_TABLE"]
EXPORT_BUCKET = os.environ["EXPORT_BUCKET"]
client = boto3.client("timestream-query")
s3 = boto3.client("s3")


def origin(_, __):
    yesterday = date.today() - timedelta(days=1)

    query = f"""
    UNLOAD (
        SELECT *
        FROM "{TIMESTREAM_DB_NAME}"."{USER_RESULT_TABLE}"
        WHERE time BETWEEN bin(now(), 1d) - 1d AND bin(now(), 1d)
    ) TO 's3://{EXPORT_BUCKET}/origin/{yesterday.strftime('%Y-%m-%d')}/{USER_RESULT_TABLE}'
    """
    try:
        client.query(QueryString=query)
    except Exception as e:
        print("query = " + re.sub("\s+", " ", query))
        raise e
    return None


def aggregate(_, __):
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    with open(Path(__file__).with_name("pokemon_names.json"), "rt") as fr:
        pokemon_names = json.load(fr)

    with tempfile.TemporaryDirectory() as tmpdirname:
        query = f"""
        SELECT pokemon, date(time) AS date, picked_win, picked_lose, picked_total, banned, match_total
        FROM "{TIMESTREAM_DB_NAME}"."{POKEMON_AGGREGATION_TABLE}"
        WHERE time = bin(now(), 1d) - 1d AND measure_name = 'aggregate_by_pokemon'
        ORDER BY picked_total + banned DESC
        """
        response = client.query(QueryString=query)

        tmpfile = os.path.join(tmpdirname, "tmp.csv")
        with open(tmpfile, "wt") as fw:
            writer = csv.writer(fw)
            writer.writerow(["ポケモン", "英語名", "日付", "勝利数", "敗戦数", "ピック数", "使用禁止数", "対戦総数"])
            for row in response["Rows"]:
                record = [data["ScalarValue"] for data in row["Data"]]
                record.insert(0, pokemon_names[record[0]])
                writer.writerow(record)
        s3.upload_file(
            tmpfile, Bucket=EXPORT_BUCKET, Key=f"aggregation/{yesterday}/aggregate_by_pokemon_{yesterday}.csv"
        )
        print("aggregate_by_pokemon.csv completed.")

        query = f"""
        SELECT pokemon, move1, move2, date(time) AS date, picked_win, picked_lose, picked_total, match_total
        FROM "{TIMESTREAM_DB_NAME}"."{POKEMON_AGGREGATION_TABLE}"
        WHERE time = bin(now(), 1d) - 1d AND measure_name = 'aggregate_by_pokemon_move'
        ORDER BY picked_total DESC
        """
        response = client.query(QueryString=query)

        tmpfile = os.path.join(tmpdirname, "tmp.csv")
        with open(tmpfile, "wt") as fw:
            writer = csv.writer(fw)
            writer.writerow(["ポケモン", "英語名", "技1", "技2", "日付", "勝利数", "敗戦数", "ピック数", "対戦総数"])
            for row in response["Rows"]:
                record = [data["ScalarValue"] for data in row["Data"]]
                record.insert(0, pokemon_names[record[0]])
                writer.writerow(record)

        s3.upload_file(
            tmpfile, Bucket=EXPORT_BUCKET, Key=f"aggregation/{yesterday}/aggregate_by_pokemon_move_{yesterday}.csv"
        )
        print("aggregate_by_pokemon_move.csv completed.")

        query = f"""
        SELECT match_id, pick_order, date(time) AS date, winner, banned_pokemon
        FROM "{TIMESTREAM_DB_NAME}"."{POKEMON_AGGREGATION_TABLE}"
        WHERE time = bin(now(), 1d) - 1d AND measure_name = 'aggregate_match'
        ORDER BY match_id
        """
        response = client.query(QueryString=query)

        tmpfile = os.path.join(tmpdirname, "tmp.csv")
        with open(tmpfile, "wt") as fw:
            writer = csv.writer(fw)
            writer.writerow(["試合ID", "ピック順", "日付", "勝利チーム", "使用禁止ポケモン"])
            for row in response["Rows"]:
                record = [data["ScalarValue"] for data in row["Data"]]
                record[3] = "先攻" if record[3] == "first" else "後攻"
                record[4] = pokemon_names[record[4]]
                writer.writerow(record)
        s3.upload_file(tmpfile, Bucket=EXPORT_BUCKET, Key=f"aggregation/{yesterday}/aggregate_match_{yesterday}.csv")
        print("aggregate_match.csv completed.")
