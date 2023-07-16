from fastapi import APIRouter, Depends, HTTPException, Form
from typing_extensions import Annotated
from ..dependencies import get_db
from ..database import Session
from ..utils import value_utils as value
from .. import schemas
from ..constant import *

router = APIRouter(
    prefix="/value",
    tags=["value"],
    # dependencies=[Depends(get_db)],
    # responses={404: {"description": "Not found"}},
)

SessionDep = Annotated[Session, Depends(get_db)]

@router.post("/line")
async def get_linechart(
    db: SessionDep,
    selectedType: str,
):
    
    pos_day, pos_season = value.get_prod_pos(db=db, selectedType=selectedType)
    value_day, value_season = value.get_prod_value(db=db, selectedType=selectedType)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "title": "商品持仓市值",
            "chart1": pos_day,
            "chart2": pos_season,
            "chart3": value_day,
            "chart4": value_season,
        }
    }