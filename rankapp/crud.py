from .database import Session
from .models import RankEntry
from . import schemas
from sqlalchemy import select, and_, func

import re

import altair as alt
import numpy as np
import pandas as pd

import json


def get_rank_entries(db: Session, rank_query: schemas.RankQuery):
    query = (
        select(RankEntry).where(
            and_(
                RankEntry.instrumentID == rank_query.instrumentID,
                RankEntry.date == rank_query.date,
                RankEntry.exchange == rank_query.exchange,
            )
        )
        .order_by(RankEntry.rank)
    )

    result = db.execute(query).all()
    return [query for (query, ) in result]

def get_instrument_type(db: Session):
    query = (
        select(RankEntry.instrumentType).distinct()
    )
    
    result = db.execute(query).all()
    return [type for (type, ) in result]

def get_instrument_id(db: Session, selected_type: str):
    query = (
        select(RankEntry.instrumentID).distinct()
    )
    result = db.execute(query).all()
    
    return [id for (id, ) in result if re.search(f'^{selected_type}[0-9]*$', id)]


def get_chart_html(db:Session, rank_query: schemas.RankQuery):
    query_long = (
        select(func.sum(RankEntry.volume), RankEntry.volumetype, RankEntry.date)
        .where(
            and_(
                RankEntry.instrumentID == rank_query.instrumentID,
                RankEntry.exchange == rank_query.exchange,
            )
        )
        .group_by(RankEntry.volumetype, RankEntry.date)          
    )   
    
    result = db.execute(query_long).all()
    date_list = []
    sum_list = []
    type_list = []

    for (sum, type, date, ) in result:
        date_list.append(date)
        sum_list.append(sum)
        type_list.append(type)

    source = pd.DataFrame({
        'date': date_list,
        'sum': sum_list,
        'type': type_list
    })

    source['date'] = pd.to_datetime(source['date'])
    source['type'] = [each.value for each in (source['type'])]

    p1 = alt.Chart(source).mark_line().encode(
        alt.X('date:T', axis=alt.Axis(format="%Y-%m-%d")),
        y='sum',
        color='type',
        tooltip=['date', 'sum', 'type']
    ).properties(
        width=800,
        height=500
    ).add_selection(
        alt.selection_single()
    ).interactive()

    return json.loads(p1.to_json())
