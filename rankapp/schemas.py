# from typing import List, Union
from pydantic import BaseModel
import datetime

class RankQuery(BaseModel):
    contractID: str
    date: datetime.date
    # ex: str

class NetPosQuery(BaseModel):
    contractType: str
    company: str