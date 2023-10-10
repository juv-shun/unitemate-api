import csv
import json
import os
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
    """APIで受信した生データをS3にバックアップする。"""
    with open(Path(__file__).parent / "sql" / "origin.sql", "rt") as fr:
        query = fr.read().format(
            db=TIMESTREAM_DB_NAME,
            table=ORIGIN_TABLE,
            bucket=EXPORT_S3_BUCKET,
            date=(date.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
        )
    client.query(QueryString=query)


def aggregate(_, __):
    """スケジュールクエリでテーブルに出力された集計結果をCSVファイルに変換してGCSにエクスポートする。"""

    # ポケモン英語名 -> 日本語名に変換するための辞書情報取得
    # FIXME APIで最初から日本語名で受信するように仕様変更したい。
    with open(Path(__file__).with_name("pokemon_names.json"), "rt") as fr:
        pokemon_names = json.load(fr)

    # namespaceの種類を取得
    query = f"""
    SELECT DISTINCT namespace
    FROM "{TIMESTREAM_DB_NAME}"."{AGGREGATION_RESULT_TABLE}"
    WHERE time = bin(now(), 1d) - 1d
    """
    response = client.query(QueryString=query)
    namespaces = [row["Data"][0]["ScalarValue"] for row in response["Rows"]]

    aggregations = [
        {
            "name": "aggregate_by_pokemon",
            "csv_header": [
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
            ],
        },
        {
            "name": "aggregate_by_pokemon_move",
            "csv_header": [
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
            ],
        },
    ]

    bucket = storage.Client().bucket(EXPORT_GCS_BUCKET)
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    with tempfile.TemporaryDirectory() as tmpdirname:
        for namespace in namespaces:
            for agg in aggregations:
                with open(Path(__file__).parent / "sql" / f"{agg['name']}.sql", "rt") as fr:
                    query = fr.read().format(
                        db=TIMESTREAM_DB_NAME,
                        table=AGGREGATION_RESULT_TABLE,
                        namespace=namespace,
                    )
                response = client.query(QueryString=query)

                tmpfile = os.path.join(tmpdirname, "tmp.csv")
                with open(tmpfile, "wt") as fw:
                    writer = csv.writer(fw)
                    writer.writerow(agg["csv_header"])
                    for row in response["Rows"]:
                        record = [data.get("ScalarValue") for data in row["Data"]]
                        record.insert(0, pokemon_names[record[0]])
                        writer.writerow(record)
                blob = bucket.blob(f"{namespace}/{agg['name']}/{agg['name']}_{yesterday}.csv")
                blob.upload_from_filename(tmpfile)
                print(f"{agg['name']}_{yesterday}.csv completed.")
