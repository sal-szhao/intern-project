import uvicorn

from typing import List
from typing_extensions import Annotated

from fastapi import Depends, FastAPI, HTTPException, status, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from . import crud, models, schemas
from .database import Session

import datetime


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
    selectedType: Annotated[str, Form()]="IF",
    selectedID: Annotated[str, Form()]="IF2307", 
    selectedDate: Annotated[datetime.date, Form()]='2023-06-14', 
    selectedExchange: Annotated[str, Form()]='CFFEX',
    db: Session = Depends(get_db)
):

    # Retrieve data from the database.
    rank_query = schemas.RankQuery(instrumentID=selectedID, date=selectedDate, exchange=selectedExchange)
    net_pos_query = schemas.NetPosDaily(instrumentID=selectedID, date=selectedDate)

    entries, volume_sums, change_sums = crud.get_rank_entries(db=db, rank_query=rank_query)
    if not entries:
        raise HTTPException(status_code=404, detail='Item not found')
    instrumentTypes = crud.get_instrument_type(db=db)
    instrumentIDs = crud.get_instrument_id(db=db, selected_type=selectedType)
    barchartlong_html= crud.get_barchart_html(db=db, rank_query=rank_query, target_type=schemas.VolumeType.long)
    barchartshort_html= crud.get_barchart_html(db=db, rank_query=rank_query, target_type=schemas.VolumeType.short)
    long_dict, short_dict, long_sum, short_sum = crud.get_net_positions_daily(db=db, net_pos_query=net_pos_query)

    # Render the template.
    return templates.TemplateResponse("rank.html", {
        "request": request,
        "entries": entries,
        "volume_sums": volume_sums,
        "change_sums": change_sums,
        "instrument_types": instrumentTypes,
        "instrument_IDs": instrumentIDs,
        "selected_type": selectedType,
        "selected_ID": selectedID,
        "selected_date": selectedDate,
        "selected_exchange": selectedExchange,
        "barchartlong_html": barchartlong_html,
        "barchartshort_html": barchartshort_html,
        "long_net_pos_dict": long_dict,
        "short_net_pos_dict": short_dict,
        "long_sum": long_sum,
        "short_sum": short_sum
    })


@app.get("/net", response_class=HTMLResponse)
@app.post("/net", response_class=HTMLResponse)
async def net(
    request: Request,
    selectedType: Annotated[str, Form()]="RB",
    selectedName: Annotated[str, Form()]="国泰君安", 
    db: Session = Depends(get_db)
):
    instrumentTypes = crud.get_instrument_type(db=db)
    companyNames = crud.get_company_name(db=db)

    net_pos_query = schemas.NetPosQuery(instrumentType=selectedType, companyName=selectedName)
    net_long_table, net_short_table, net_long_sum, net_short_sum = crud.get_net_pos_rank(db=db, selectedType=selectedType)
    linechart_company = crud.get_linechart_company(db=db, net_pos_query=net_pos_query)    
    if not linechart_company:
        raise HTTPException(status_code=404, detail='Item not found')
    linechart_total = crud.get_linechart_total(db=db, selectedType=selectedType)    

    return templates.TemplateResponse("net_positions.html", {
        "request": request,
        "instrument_types": instrumentTypes,
        "company_names": companyNames,
        "selected_type": selectedType,
        "selected_name": selectedName,
        "linechart_company": linechart_company,
        "linechart_total": linechart_total,
        "net_long_table": net_long_table,
        "net_short_table": net_short_table,
        "net_long_sum": net_long_sum,
        "net_short_sum": net_short_sum
    })

@app.exception_handler(404)
async def http_exception_handler(request, exc):
    return templates.TemplateResponse("errors/404.html", {"request": request})

