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


class PokemonEnum(str, Enum):
    absol = "absol"
    aegislash = "aegislash"
    azumarill = "azumarill"
    blastoise = "blastoise"
    blaziken = "blaziken"
    blissey = "blissey"
    buzzwole = "buzzwole"
    chandelure = "chandelure"
    charizard = "charizard"
    cinderace = "cinderace"
    clefable = "clefable"
    comfey = "comfey"
    cramorant = "cramorant"
    crustle = "crustle"
    decidueye = "decidueye"
    delphox = "delphox"
    dodrio = "dodrio"
    dragapult = "dragapult"
    dragonite = "dragonite"
    duraludon = "duraludon"
    eldegoss = "eldegoss"
    espeon = "espeon"
    garchomp = "garchomp"
    gardevoir = "gardevoir"
    gengar = "gengar"
    glaceon = "glaceon"
    goodra = "goodra"
    greedent = "greedent"
    greninja = "greninja"
    gyarados = "gyarados"
    hoopa = "hoopa"
    inteleon = "inteleon"
    lapras = "lapras"
    leafeon = "leafeon"
    lucario = "lucario"
    machamp = "machamp"
    mamoswine = "mamoswine"
    meowscarada = "meowscarada"
    metagross = "metagross"
    mew = "mew"
    mewtwo_x = "mewtwo_x"
    mewtwo_y = "mewtwo_y"
    mimikyu = "mimikyu"
    mr_mime = "mr_mime"
    ninetales = "ninetales"
    pikachu = "pikachu"
    sableye = "sableye"
    scizor = "scizor"
    scyther = "scyther"
    slowbro = "slowbro"
    snorlax = "snorlax"
    sylveon = "sylveon"
    talonflame = "talonflame"
    trevenant = "trevenant"
    tsareena = "tsareena"
    tyranitar = "tyranitar"
    umbreon = "umbreon"
    urshifu = "urshifu"
    venusaur = "venusaur"
    wigglytuff = "wigglytuff"
    zacian = "zacian"
    zeraora = "zeraora"
    zoroark = "zoroark"
    empty = "empty"


class MatchUserResult(BaseModel):
    class MoveModel(BaseModel):
        move1: str
        move2: str

    namespace: str = "default"
    match_id: str
    user_id: str
    winner: WinnerEnum
    datetime: _datetime
    pokemon: PokemonEnum
    moves: Optional[MoveModel] = None
    is_first_pick: bool
    banned_pokemons: Optional[List[PokemonEnum]] = None
    rate: Optional[float] = None

    @field_validator("datetime")
    @classmethod
    def validate_datetime(cls, value: _datetime) -> _datetime:
        if value < (_datetime.now(JST) - timedelta(hours=24)):
            raise ValueError("datetime must be in 24 hours.")
        return value
