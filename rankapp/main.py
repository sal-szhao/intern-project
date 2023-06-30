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

@app.get("/home/", response_class=HTMLResponse)
@app.post("/home/", response_class=HTMLResponse)
async def rank(
    request: Request,
    selectedType: Annotated[str, Form()]="IF",
    selectedID: Annotated[str, Form()]="IF2306", 
    selectedDate: Annotated[datetime.date, Form()]='2023-06-14', 
    selectedExchange: Annotated[str, Form()]='CFFEX',
    db: Session = Depends(get_db)
):

    rank_query = schemas.RankQuery(instrumentID=selectedID, date=selectedDate, exchange=selectedExchange)
    entries = crud.get_rank_entries(db=db, rank_query=rank_query)
    instrumentTypes = crud.get_instrument_type(db=db)
    instrumentIDs = crud.get_instrument_id(db=db, selected_type=selectedType)
    chart_html = crud.get_chart_html(db=db, rank_query=rank_query)

    # Drawing the chart using altair.
    return templates.TemplateResponse("rank.html", {
        "request": request,
        "entries": entries,
        "instrument_types": instrumentTypes,
        "instrument_IDs": instrumentIDs,
        "exchanges": ["CFFEX", "SHFE"],
        "selected_type": selectedType,
        "selected_ID": selectedID,
        "selected_date": selectedDate,
        "selected_exchange": selectedExchange,
        "chart_html": chart_html
    })

