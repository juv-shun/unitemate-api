from datetime import datetime as _datetime
from datetime import timedelta, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, field_validator

JST = timezone(timedelta(hours=+9), "JST")


class WinnerEnum(str, Enum):
    first = "first"
    second = "second"
    invalid = "invalid"


class MatchUserResult(BaseModel):
    class MoveModel(BaseModel):
        move1: str
        move2: str

    namespace: str = "default"
    match_id: str
    user_id: str
    winner: WinnerEnum
    datetime: _datetime
    pokemon: str
    moves: Optional[MoveModel] = None
    is_first_pick: bool
    banned_pokemons: Optional[List[str]] = None
    rate: Optional[float] = None

    @field_validator("datetime")
    @classmethod
    def validate_datetime(cls, value: _datetime) -> _datetime:
        if value < (_datetime.now(JST) - timedelta(hours=24)):
            raise ValueError("datetime must be in 24 hours.")
        return value
