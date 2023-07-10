from fastapi import APIRouter, Depends, HTTPException, Form
from typing_extensions import Annotated
from ..dependencies import get_db
from ..database import Session
from ..utils import common_utils as common
from ..utils import rank_utils as rank
from .. import schemas
import datetime


router = APIRouter(
    prefix="/rank",
    tags=["rank"],
    dependencies=[Depends(get_db)],
    # responses={404: {"description": "Not found"}},
)

@router.get("/f_id")
async def get_contract_ID(
    selectedType: str='cu',
    db: Session=Depends(get_db),
):

    contractIDs = common.get_contract_id(db=db, selected_type=selectedType)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": contractIDs,
    }


@router.get("/f_date")
async def get_date(
    selectedID: str='cu2307',
    db: Session=Depends(get_db),
):

    contractDate = common.get_date(db=db, selected_id=selectedID)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": contractDate,
    }
    

@router.post("/table")  
async def get_table(
    selectedID: Annotated[str, Form()]="cu2307", 
    selectedDate: Annotated[datetime.date, Form()]='2023-06-29', 
    db: Session = Depends(get_db),
):

    rank_query = schemas.RankQuery(contractID=selectedID, date=selectedDate)
    table_b = rank.get_rank_entries(db=db, rank_query=rank_query, volType='b')
    table_s = rank.get_rank_entries(db=db, rank_query=rank_query, volType='s')

    # if not entries:
    #     raise HTTPException(status_code=404, detail='Item not found')
    # contractTypes = crud.get_contract_type(db=db)
    # contractIDs = crud.get_contract_id(db=db, selected_type=selectedType)

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
      

@router.post("/bar")  
async def get_bar(
    selectedID: Annotated[str, Form()]="cu2307", 
    selectedDate: Annotated[datetime.date, Form()]='2023-06-29', 
    db: Session = Depends(get_db),
):
    
    rank_query = schemas.RankQuery(contractID=selectedID, date=selectedDate)
    bar_b = rank.get_barchart_rank(db=db, rank_query=rank_query, volType='b')
    bar_s = rank.get_barchart_rank(db=db, rank_query=rank_query, volType='s')

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "chart1": bar_b,
            "chart2": bar_s,
        }
    }

@router.post("/line")  
async def get_line(
    selectedID: Annotated[str, Form()]="cu2307", 
    db: Session = Depends(get_db),
):
    
    line = rank.get_linechart_rank(db=db, selectedID=selectedID)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "chart1": line,
        }
    }
