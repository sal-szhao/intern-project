from fastapi import Form
from pydantic import BaseModel
import datetime
from typing_extensions import Annotated

class RankQuery(BaseModel):
    contractID: Annotated[str, Form()] = "cu2307"
    date: Annotated[datetime.date, Form()]= "2023-06-29"
    # ex: str

class NetPosQuery(BaseModel):
    contractType: Annotated[str, Form()] = "rb"
    company: Annotated[str, Form()] = "国泰君安" 

class MonthQuery(BaseModel):
    contractType: Annotated[str, Form()] = "rb"
    contractMonth: Annotated[str, Form()] = "09"
