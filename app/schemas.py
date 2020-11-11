import datetime
from typing import List
from pydantic import Field, BaseModel


class MatchSchemas(BaseModel):
    name: str = Field(..., example='OCLR β教练赛')
    description: str = Field(None, example='谁会是最强教练？')
    member: List[str] = Field(..., example=['milk-tea', 'im_a_burger_fox', 'silly me'])
    adder_qq: int = Field(...)


class PlaceBetSchemas(BaseModel):
    qq: int = Field(...)
    amount: int = Field(...)
    target: str
