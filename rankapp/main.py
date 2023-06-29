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
    date: Annotated[datetime.date, Form()]='2023-06-14', 
    instrumentID: Annotated[str, Form()]="IF2306", 
    exchange: Annotated[str, Form()]='CFFEX',
    instrumentType: Annotated[str, Form()]='IF',
    db: Session = Depends(get_db)
):
    
    date = datetime.datetime.strptime('2023-06-14', '%Y-%m-%d')
    rank_query = schemas.RankQuery(instrumentID=instrumentID, date=date, exchange=exchange)
    entries = crud.get_rank_entries(db=db, rank_query=rank_query)
    
    return templates.TemplateResponse("rank.html", {
        "request": request,
        "entries": entries,
        "instrument_types": ["IF", "IC"],
        "selected_type": instrumentType
    })

