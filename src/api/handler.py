import json
import os
from typing import Any, Dict

import boto3
from pydantic import ValidationError

from .models import MatchUserResult

TIMESTREAM_DB_NAME = os.environ["TIMESTREAM_DB_NAME"]
ORIGIN_TABLE = os.environ["ORIGIN_TABLE"]


def build_record(name: str, value, type: str) -> Dict[str, Any]:
    return {"Name": name, "Value": value, "Type": type}


def user_result(event, _):
    """AWS API Gateway経由で受信したリクエスト情報をもとに、Timestream DBにデータを格納する。"""

    # バリデーションチェック
    try:
        model = MatchUserResult(**json.loads(event["body"]))
    except ValidationError as e:
        print("ERROR: " + json.dumps(e.json()))
        return {"statusCode": 422, "body": e.json()}

    # Timestream DBに格納するためのレコード生成
    write_client = boto3.Session().client("timestream-write")
    record = {
        "Dimensions": [
            {"Name": "namespace", "Value": model.namespace},
            {"Name": "user_id", "Value": model.user_id},
            {"Name": "match_id", "Value": model.match_id},
        ],
        "MeasureName": "user_result",
        "MeasureValueType": "MULTI",
        "Time": str(int(model.datetime.timestamp() * 1000)),
        "MeasureValues": [
            build_record("winner", model.winner, "VARCHAR"),
            build_record("pokemon", model.pokemon, "VARCHAR"),
            build_record("is_first_pick", str(model.is_first_pick), "BOOLEAN"),
        ],
    }
    if model.moves:
        record["MeasureValues"].append(build_record("move1", str(model.moves.move1), "VARCHAR"))
        record["MeasureValues"].append(build_record("move2", str(model.moves.move2), "VARCHAR"))
    if model.banned_pokemons:
        for i, pokemon in enumerate(model.banned_pokemons):
            record["MeasureValues"].append(build_record(f"banned_pokemon_{i}", pokemon, "VARCHAR"))
    if model.rate:
        record["MeasureValues"].append(build_record("rate", str(int(model.rate)), "BIGINT"))

    # Timestream DBに格納
    try:
        write_client.write_records(
            DatabaseName=TIMESTREAM_DB_NAME,
            TableName=ORIGIN_TABLE,
            CommonAttributes={},
            Records=[record],
        )
    except write_client.exceptions.RejectedRecordsException as err:
        print("[ERROR] Records insertion failed.")
        for rr in err.response["RejectedRecords"]:
            print(f"Rejected Index {rr['RecordIndex']}: {rr['Reason']}")
            print(f"Record: {json.dumps(record)}")
            raise

    return {"statusCode": 201, "body": None}
