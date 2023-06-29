# from typing import List, Union
from pydantic import BaseModel
import datetime

class RankQuery(BaseModel):
    instrumentID: str
    exchange: str
    date: datetime.date


