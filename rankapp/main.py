import uvicorn
import datetime
from typing import List
from typing_extensions import Annotated

from fastapi import Depends, FastAPI, HTTPException, status, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from . import crud, models, schemas
from .database import Session



app = FastAPI()
app.mount("/static", StaticFiles(directory="rankapp/static"), name="static")
templates = Jinja2Templates(directory='rankapp/templates')

# Session dependency.
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
@app.post("/", response_class=HTMLResponse)
async def rank(
    request: Request,
    selectedType: Annotated[str, Form()]="cu",
    selectedID: Annotated[str, Form()]="cu2307", 
    selectedDate: Annotated[datetime.date, Form()]='2023-06-29', 
    db: Session = Depends(get_db)
):

    # Retrieve data from the database.
    rank_query = schemas.RankQuery(contractID=selectedID, date=selectedDate)
    # net_pos_query = schemas.NetPosDaily(instrumentID=selectedID, date=selectedDate)

    entries, sums = crud.get_rank_entries(db=db, rank_query=rank_query)
    if not entries:
        raise HTTPException(status_code=404, detail='Item not found')
    contractTypes = crud.get_contract_type(db=db)
    contractIDs = crud.get_contract_id(db=db, selected_type=selectedType)
    barChartLong, barChartShort= crud.get_barchart_html(db=db, rank_query=rank_query)

    # Render the template.
    return templates.TemplateResponse("rank.html", {
        "request": request,
        "entries": entries,
        "sums": sums,
        "contract_types": contractTypes,
        "contract_IDs": contractIDs,
        "selected_type": selectedType,
        "selected_ID": selectedID,
        "selected_date": selectedDate,
        "bar_chart_long": barChartLong,
        "bar_chart_short": barChartShort,
    })


@app.get("/net", response_class=HTMLResponse)
@app.post("/net", response_class=HTMLResponse)
async def net(
    request: Request,
    selectedType: Annotated[str, Form()]="rb",
    selectedName: Annotated[str, Form()]="国泰君安", 
    db: Session = Depends(get_db)
):
    
    contractTypes = crud.get_contract_type(db=db)
    companyNames = crud.get_company_name(db=db)

    net_pos_query = schemas.NetPosQuery(contractType=selectedType, company=selectedName)
    netRank = crud.get_net_rank(db=db, selectedType=selectedType)
    lineChartCompany = crud.get_linechart_company(db=db, net_pos_query=net_pos_query)    
    lineChartTotal = crud.get_linechart_total(db=db, selectedType=selectedType)    

    return templates.TemplateResponse("net.html", {
        "request": request,
        "contract_types": contractTypes,
        "company_names": companyNames,
        "selected_type": selectedType,
        "selected_name": selectedName,
        "line_chart_company": lineChartCompany,
        "line_chart_total": lineChartTotal,
        "net_rank": netRank,
    })

@app.exception_handler(404)
async def http_exception_handler(request, exc):
    return templates.TemplateResponse("errors/404.html", {"request": request})

