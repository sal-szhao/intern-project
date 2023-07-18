from fastapi import APIRouter, Depends, HTTPException, Form
from typing_extensions import Annotated
from ..dependencies import get_db
from ..database import Session
from ..utils import month_utils as month
from .. import schemas
from ..constant import *

router = APIRouter(
    prefix="/month",
    tags=["month"],
)

SessionDep = Annotated[Session, Depends(get_db)]


@router.post("/table")
async def get_table(
    db: SessionDep,
    month_query: schemas.MonthQuery,
):

    table = month.get_increase_percentage(db=db, month_query=month_query)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "title": f"{INS_TYPE_TRANS[month_query.contractType]}{month_query.contractMonth}合约月度涨跌统计",
            "list": table,
        }
    }