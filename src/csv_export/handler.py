import csv
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from google.cloud import storage

TIMESTREAM_DB_NAME = os.environ["TIMESTREAM_DB_NAME"]
ORIGIN_TABLE = os.environ["ORIGIN_TABLE"]
AGGREGATION_RESULT_TABLE = os.environ["AGGREGATION_RESULT_TABLE"]
EXPORT_S3_BUCKET = os.environ["EXPORT_S3_BUCKET"]
EXPORT_GCS_BUCKET = os.environ["EXPORT_GCS_BUCKET"]
client = boto3.client("timestream-query")


def origin(event, __):
    """APIで受信した生データをS3にバックアップする。"""
    now = datetime.fromisoformat(event.get("time").replace("Z", "+00:00")) if event.get("time") else datetime.now()
    with open(Path(__file__).parent / "sql" / "origin.sql", "rt") as fr:
        query = fr.read().format(
            db=TIMESTREAM_DB_NAME,
            table=ORIGIN_TABLE,
            bucket=EXPORT_S3_BUCKET,
            yesterday=(now - timedelta(days=1)).strftime("%Y-%m-%d"),
        )
    client.query(QueryString=query)


def aggregate(event, __):
    """スケジュールクエリでテーブルに出力された集計結果をCSVファイルに変換してGCSにエクスポートする。"""
    now = datetime.fromisoformat(event.get("time").replace("Z", "+00:00")) if event.get("time") else datetime.now()
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # namespaceの種類を取得
    query = f"""
    SELECT DISTINCT namespace
    FROM "{TIMESTREAM_DB_NAME}"."{AGGREGATION_RESULT_TABLE}"
    WHERE time = '{yesterday}'
    """
    response = client.query(QueryString=query)
    namespaces = [row["Data"][0]["ScalarValue"] for row in response["Rows"]]

    # 出力ファイルの設定を読み込む
    with open(Path(__file__).with_name("aggregation_patterns.json"), "rt") as fr:
        aggregations = json.load(fr)

    bucket = storage.Client().bucket(EXPORT_GCS_BUCKET)
    with tempfile.TemporaryDirectory() as tmpdirname:
        for namespace in namespaces:
            for agg in aggregations:
                # TimeStreamからレコード取得
                with open(Path(__file__).parent / "sql" / f"{agg['name']}.sql", "rt") as fr:
                    query = fr.read().format(
                        db=TIMESTREAM_DB_NAME,
                        table=AGGREGATION_RESULT_TABLE,
                        namespace=namespace,
                        yesterday=yesterday,
                    )
                response = client.query(QueryString=query)

                # CSVファイル作成
                tmpfile = os.path.join(tmpdirname, "tmp.csv")
                with open(tmpfile, "wt") as fw:
                    writer = csv.writer(fw)
                    writer.writerow(agg["csv_header"])
                    for row in response["Rows"]:
                        record = [data.get("ScalarValue") for data in row["Data"]]
                        writer.writerow(record)

                # GCSにアップロード
                blob = bucket.blob(f"{namespace}/{agg['name']}/{agg['name']}_{yesterday}.csv")
                blob.upload_from_filename(tmpfile)
                print(f"{agg['name']}_{yesterday}.csv for {yesterday} completed.")
