from fastapi import APIRouter, Depends, HTTPException, Form
from typing_extensions import Annotated
from ..dependencies import get_db
from ..database import Session
from ..utils import common_utils as common
from ..utils import net_utils as net
from .. import schemas
from ..constant import *
import datetime

router = APIRouter(
    prefix="/net",
    tags=["net"],
    dependencies=[Depends(get_db)],
    # responses={404: {"description": "Not found"}},
)

@router.post("/line")
async def get_linechart(
    selectedType: Annotated[str, Form()]="rb",
    selectedName: Annotated[str, Form()]="国泰君安", 
    db: Session = Depends(get_db)
):

    net_pos_query = schemas.NetPosQuery(contractType=selectedType, company=selectedName)
    line_company = net.get_linechart_net_company(db=db, net_pos_query=net_pos_query)
    line_total = net.get_linechart_net_total(db=db, selectedType=selectedType)    
    line_k = net.get_k_linechart_net(db=db, selectedType=selectedType)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "title": f"{INS_TYPE_TRANS[selectedType]}净持仓曲线",
            "chart1": line_k,
            "chart2": line_company,
            "chart3": line_total,
        }
    }

@router.post("/table")
async def get_table(
    selectedType: Annotated[str, Form()]="rb",
    db: Session = Depends(get_db)
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
