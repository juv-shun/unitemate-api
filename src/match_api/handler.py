import json
import os

import arrow
import boto3
from pydantic import ValidationError

from .models import MatchBasicResult, MatchUserResult

dynamodb = boto3.resource("dynamodb")
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


def user_result(event, _):
    try:
        model = MatchUserResult(**json.loads(event["body"]))
    except ValidationError as e:
        return {"statusCode": 422, "body": json.dumps(e.errors())}

    table = dynamodb.Table(DYNAMODB_TABLE)
    table.put_item(
        Item={
            "namespace": model.namespace,
            "match_id": model.match_id,
            "namespace_user_id": f"{model.namespace}#{model.user_id}",
            "result": model.result,
            "timestamp": int(model.datetime.timestamp()),
            "pokemon": model.pokemon,
            "namespace_pokemon": f"{model.namespace}#{model.pokemon}",
            "role": model.role,
            "moves": dict(model.moves) if model.moves else None,
            "ttl": arrow.get(model.datetime).shift(days=180).int_timestamp,
        }
    )

    return {"statusCode": 201, "body": None}


def basic_result(event, _):
    try:
        model = MatchBasicResult(**json.loads(event["body"]))
    except ValidationError as e:
        return {"statusCode": 422, "body": json.dumps(e.errors())}

    table = dynamodb.Table(DYNAMODB_TABLE)
    table.put_item(
        Item={
            "namespace": model.namespace,
            "match_id": model.match_id,
            "namespace_user_id": f"{model.namespace}#N/A",
            "timestamp": int(model.datetime.timestamp()),
            "teams": [dict(team_data) for team_data in model.teams] if model.teams else None,
            "ttl": arrow.get(model.datetime).shift(days=180).int_timestamp,
        }
    )

    return {"statusCode": 201, "body": None}
