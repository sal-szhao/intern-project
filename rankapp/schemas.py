# from typing import List, Union
from pydantic import BaseModel
import datetime
import enum

class VolumeType(enum.Enum):
    trading = 'trading'
    long = 'long'
    short = 'short'

class RankQuery(BaseModel):
    instrumentID: str
    exchange: str
    date: datetime.date


class NetPosDaily(BaseModel):
    instrumentID: str
    date: datetime.date

class NetPosQuery(BaseModel):
    instrumentType: str
    companyName: str