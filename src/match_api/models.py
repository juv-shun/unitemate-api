from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ResultEnum(str, Enum):
    win = "win"
    lose = "lose"


class RoleEnum(str, Enum):
    top_carry = "top_carry"
    top_support = "top_support"
    bottom_carry = "bottom_carry"
    bottom_support = "bottom_support"
    jungle = "jungle"


class PokemonEnum(str, Enum):
    absol = "absol"
    aegislash = "aegislash"
    azumarill = "azumarill"
    blastoise = "blastoise"
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
    hoopa = "hoopa"
    inteleon = "inteleon"
    lapras = "lapras"
    leafeon = "leafeon"
    lucario = "lucario"
    machamp = "machamp"
    mamoswine = "mamoswine"
    mew = "mew"
    mewtwo_x = "mewtwo_x"
    mewtwo_y = "mewtwo_y"
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


class MatchUserResult(BaseModel):
    class MoveModel(BaseModel):
        move1: int = Field(gte=1, lte=2)
        move2: int = Field(gte=1, lte=2)

    namespace: str = "default"
    match_id: str
    user_id: str
    result: ResultEnum
    datetime: datetime
    pokemon: Optional[PokemonEnum] = None
    moves: MoveModel = None
    role: Optional[RoleEnum] = None


class MatchBasicResult(BaseModel):
    class TeamModel(BaseModel):
        result: ResultEnum
        is_first_pick: bool
        banned_pokemons: Optional[List[PokemonEnum]] = Field(None, min_length=1, max_length=1)
        picked_pokemons: Optional[List[PokemonEnum]] = Field(None, min_length=5, max_length=5)

    namespace: str = "default"
    match_id: str
    datetime: datetime
    teams: Optional[List[TeamModel]] = Field(None, min_length=2, max_length=2)
