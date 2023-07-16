from fastapi import APIRouter, Depends, HTTPException, Form
from typing_extensions import Annotated
from ..dependencies import get_db
from ..database import Session
from ..utils import net_utils as net
from .. import schemas
from ..constant import *

router = APIRouter(
    prefix="/net",
    tags=["net"],
    # dependencies=[Depends(get_db)],
    # responses={404: {"description": "Not found"}},
)

SessionDep = Annotated[Session, Depends(get_db)]

@router.post("/line")
async def get_linechart(
    db: SessionDep,
    net_pos_query: schemas.NetPosQuery,
):

    line_company = net.get_linechart_net_company(db=db, net_pos_query=net_pos_query)
    line_total = net.get_linechart_net_total(db=db, selectedType=net_pos_query.contractType)    
    line_k = net.get_k_linechart_net(db=db, selectedType=net_pos_query.contractType)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "title": f"{INS_TYPE_TRANS[net_pos_query.contractType]}净持仓曲线",
            "chart1": line_k,
            "chart2": line_company,
            "chart3": line_total,
        }
    }

@router.post("/table")
async def get_table(
    db: SessionDep,
    selectedType: Annotated[str, Form()]="rb",
):
    
    table_b = net.get_net_rank(db=db, selectedType=selectedType, volType='b')
    table_s = net.get_net_rank(db=db, selectedType=selectedType, volType='s')

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "table1": table_b,
            "table2": table_s,
        }
    }
