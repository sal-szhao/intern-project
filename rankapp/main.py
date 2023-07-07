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

@app.get("/")
async def getContractType(db: Session=Depends(get_db)):
    contract_types = crud.get_contract_type(db=db)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": contract_types,
    }

@app.post("/")
async def getContractID(
    selectedType: str="cu",
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
    # barChartLong, barChartShort= crud.get_barchart_html(db=db, rank_query=rank_query)

    # Render the template.
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
      


# @app.get("/net")
# @app.post("/net")
# async def net(
#     request: Request,
#     selectedType: Annotated[str, Form()]="rb",
#     selectedName: Annotated[str, Form()]="国泰君安", 
#     db: Session = Depends(get_db)
# ):
    
#     contractTypes = crud.get_contract_type(db=db)
#     companyNames = crud.get_company_name(db=db)

#     net_pos_query = schemas.NetPosQuery(contractType=selectedType, company=selectedName)
#     netRank = crud.get_net_rank(db=db, selectedType=selectedType)
#     lineChartCompany = crud.get_linechart_company(db=db, net_pos_query=net_pos_query)    
#     lineChartTotal = crud.get_linechart_total(db=db, selectedType=selectedType)    

#     return templates.TemplateResponse("net.html", {
#         "request": request,
#         "contract_types": contractTypes,
#         "company_names": companyNames,
#         "selected_type": selectedType,
#         "selected_name": selectedName,
#         "line_chart_company": lineChartCompany,
#         "line_chart_total": lineChartTotal,
#         "net_rank": netRank,
#     })

# @app.exception_handler(404)
# async def http_exception_handler(request, exc):
#     return templates.TemplateResponse("errors/404.html", {"request": request})

