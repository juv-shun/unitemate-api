import json
import os

import arrow
import boto3
from pydantic import ValidationError

from .models import MatchBanned, MatchResult

dynamodb = boto3.resource("dynamodb")
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


def result(event, _):
    try:
        model = MatchResult(**json.loads(event["body"]))
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
            "ttl": arrow.get(model.datetime).shift(days=180).int_timestamp,
        }
    )

    return {"statusCode": 201, "body": None}


def banned(event, _):
    try:
        model = MatchBanned(**json.loads(event["body"]))
    except ValidationError as e:
        return {"statusCode": 422, "body": json.dumps(e.errors())}

    table = dynamodb.Table(DYNAMODB_TABLE)
    table.put_item(
        Item={
            "namespace": model.namespace,
            "match_id": model.match_id,
            "namespace_user_id": f"{model.namespace}#N/A",
            "timestamp": int(model.datetime.timestamp()),
            "pokemon": model.pokemon,
            "namespace_pokemon": f"{model.namespace}#{model.pokemon}",
            "ttl": arrow.get(model.datetime).shift(days=180).int_timestamp,
        }
    )

    return {"statusCode": 201, "body": None}
