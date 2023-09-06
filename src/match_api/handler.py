import json
import os
from typing import Any, Dict

import boto3
from pydantic import ValidationError

from .models import MatchBasicResult, MatchUserResult

TIMESTREAM_DB_NAME = os.environ["TIMESTREAM_DB_NAME"]
USER_RESULT_TABLE = os.environ["USER_RESULT_TABLE"]
BASIC_RESULT_TABLE = os.environ["BASIC_RESULT_TABLE"]


def build_record(name: str, value, type: str) -> Dict[str, Any]:
    return {"Name": name, "Value": value, "Type": type}


def user_result(event, _):
    try:
        model = MatchUserResult(**json.loads(event["body"]))
    except ValidationError as e:
        return {"statusCode": 422, "body": json.dumps(e.errors())}
    except Exception:
        return {"statusCode": 400}

    write_client = boto3.Session().client("timestream-write")
    record = {
        "Dimensions": [
            {"Name": "namespace", "Value": model.namespace},
            {"Name": "user_id", "Value": model.user_id},
        ],
        "MeasureName": "user_result",
        "MeasureValueType": "MULTI",
        "Time": str(int(model.datetime.timestamp() * 1000)),
        "MeasureValues": [],
    }
    record["MeasureValues"].append(build_record("result", model.result, "VARCHAR"))
    if model.pokemon:
        record["MeasureValues"].append(build_record("pokemon", model.pokemon, "VARCHAR"))
    if model.role:
        record["MeasureValues"].append(build_record("role", model.role, "VARCHAR"))
    if model.moves:
        record["MeasureValues"].append(build_record("move1", str(model.moves.move1), "VARCHAR"))
        record["MeasureValues"].append(build_record("move2", str(model.moves.move2), "VARCHAR"))
    write_client.write_records(
        DatabaseName=TIMESTREAM_DB_NAME,
        TableName=USER_RESULT_TABLE,
        CommonAttributes={},
        Records=[record],
    )

    return {"statusCode": 201, "body": None}


def basic_result(event, _):
    try:
        model = MatchBasicResult(**json.loads(event["body"]))
    except ValidationError as e:
        return {"statusCode": 422, "body": json.dumps(e.errors())}
    except Exception:
        return {"statusCode": 400}

    write_client = boto3.Session().client("timestream-write")
    record = {
        "Dimensions": [
            {"Name": "namespace", "Value": model.namespace},
            {"Name": "match_id", "Value": model.match_id},
        ],
        "MeasureName": "basic_result",
        "MeasureValueType": "MULTI",
        "Time": str(int(model.datetime.timestamp() * 1000)),
        "MeasureValues": [],
    }
    if model.teams:
        for i, team in enumerate(model.teams):
            record["MeasureValues"].append(build_record(f"team{i}_result", team.result, "VARCHAR"))
            record["MeasureValues"].append(build_record(f"team{i}_is_first_pick", str(team.is_first_pick), "BOOLEAN"))
            if team.banned_pokemons:
                for j, pokemon in enumerate(team.banned_pokemons):
                    record["MeasureValues"].append(build_record(f"team{i}_banned_pokemon{j}", pokemon, "VARCHAR"))
            if team.picked_pokemons:
                for j, pokemon in enumerate(team.picked_pokemons):
                    record["MeasureValues"].append(build_record(f"team{i}_picked_pokemon{j}", pokemon, "VARCHAR"))
        write_client.write_records(
            DatabaseName=TIMESTREAM_DB_NAME,
            TableName=BASIC_RESULT_TABLE,
            CommonAttributes={},
            Records=[record],
        )

    return {"statusCode": 201, "body": None}
