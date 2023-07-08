import uvicorn
import datetime
from typing import List
from typing_extensions import Annotated
from fastapi import Depends, FastAPI, HTTPException, status, Request, Form

from . import crud, models, schemas
from .database import Session


app = FastAPI()

# Session dependency.
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@app.get("/common/f_name")
async def getContractType(
    db: Session=Depends(get_db)
):
    contract_types = crud.get_contract_type(db=db)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": contract_types,
    }

@app.get("/common/f_company")
async def getContractType(
    db: Session=Depends(get_db)
):
    companies = crud.get_company(db=db)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": companies,
    }


@app.get("/rank/f_id")
async def getContractID(
    selectedType: str='cu',
    db: Session=Depends(get_db),
):

    contractIDs = crud.get_contract_id(db=db, selected_type=selectedType)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": contractIDs,
    }


@app.get("/rank/f_date")
async def getDate(
    selectedID: str='cu2307',
    db: Session=Depends(get_db),
):

    contractDate = crud.get_date(db=db, selected_id=selectedID)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": contractDate,
    }
    

@app.post("/rank/table")  
async def rank(
    selectedID: Annotated[str, Form()]="cu2307", 
    selectedDate: Annotated[datetime.date, Form()]='2023-06-29', 
    db: Session = Depends(get_db),
):

    rank_query = schemas.RankQuery(contractID=selectedID, date=selectedDate)
    table_b = crud.get_rank_entries(db=db, rank_query=rank_query, volType='b')
    table_s = crud.get_rank_entries(db=db, rank_query=rank_query, volType='s')

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
      

@app.post("/rank/bar")  
async def rank(
    selectedID: Annotated[str, Form()]="cu2307", 
    selectedDate: Annotated[datetime.date, Form()]='2023-06-29', 
    db: Session = Depends(get_db),
):
    
    rank_query = schemas.RankQuery(contractID=selectedID, date=selectedDate)
    bar_b = crud.get_barchart_rank(db=db, rank_query=rank_query, volType='b')
    bar_s = crud.get_barchart_rank(db=db, rank_query=rank_query, volType='s')

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "chart2": bar_b,
            "chart3": bar_s,
        }
    }


@app.post("/net/line")
async def net(
    selectedType: Annotated[str, Form()]="rb",
    selectedName: Annotated[str, Form()]="国泰君安", 
    db: Session = Depends(get_db)
):

    net_pos_query = schemas.NetPosQuery(contractType=selectedType, company=selectedName)
    line_company = crud.get_linechart_net_company(db=db, net_pos_query=net_pos_query)
    line_total = crud.get_linechart_net_total(db=db, selectedType=selectedType)    

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": {
            "chart2": line_company,
            "chart3": line_total,
        }
    }

@app.post("/net/table")
async def net(
    selectedType: Annotated[str, Form()]="rb",
    db: Session = Depends(get_db)
):
    
    table_b = crud.get_net_rank(db=db, selectedType=selectedType, volType='b')
    table_s = crud.get_net_rank(db=db, selectedType=selectedType, volType='s')

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
    
    

# @app.exception_handler(404)
# async def http_exception_handler(request, exc):
#     return templates.TemplateResponse("errors/404.html", {"request": request})

