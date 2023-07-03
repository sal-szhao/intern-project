from .database import Session
from .models import RankEntry, VolumeType
from . import schemas
from sqlalchemy import select, and_, or_, func

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
                # RankEntry.exchange == rank_query.exchange,
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


def get_linechart_html(db:Session, rank_query: schemas.RankQuery):
    query = (
        select(func.sum(RankEntry.volume), RankEntry.volumetype, RankEntry.date)
        .where(
            and_(
                RankEntry.instrumentID == rank_query.instrumentID,
                # RankEntry.exchange == rank_query.exchange,
            )
        )
        .group_by(RankEntry.volumetype, RankEntry.date)          
    )   
    
    result = db.execute(query).all()
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

def get_barchart_html(db:Session, rank_query: schemas.RankQuery):
    source = dict()
    temp = dict()

    for target_type in [VolumeType.long, VolumeType.short]:
        query = (
            select(RankEntry.volume, RankEntry.companyname, RankEntry.change)
            .where(
                and_(
                    RankEntry.instrumentID == rank_query.instrumentID,
                    RankEntry.date == rank_query.date,
                    RankEntry.volumetype == target_type,
                )
            )
            .order_by(RankEntry.rank)
        )   

        result = db.execute(query).all()
        volume_list, type_list, name_list = [], [], []

        for (volume, companyname, change, ) in result:
            volume_list.append(volume)
            type_list.append(target_type.value)
            name_list.append(companyname)

            volume_list.append(change)
            name_list.append(companyname)
            if change >= 0:
                type_list.append("increase")
            else:
                type_list.append("decrease")

        source[target_type.value] = pd.DataFrame({
            'volume': volume_list,
            'type': type_list,
            'name': name_list
        })
        
        temp[target_type.value] = []
        for i, each in enumerate(name_list):
            if i % 2 == 1:
                continue
            temp[target_type.value].append(each)

        order = ['long', 'short', 'increase', 'decrease']
        order_num = list(range(4))
        type_order_dict = dict(zip(order, order_num))
        source[target_type.value]['type_order'] = source[target_type.value]['type'].apply(lambda x: type_order_dict[x])
    
    plong = alt.Chart(
        source['long'], 
        title=f"{rank_query.instrumentID}多头龙虎榜"
    ).transform_calculate(
        abs_volume = 'abs(datum.volume)'
    ).mark_bar().encode(
        x=alt.X('abs_volume:Q', title=""),
        y=alt.Y('name:N', title="", sort=temp['long']),
        color=alt.Color('type:N', sort=order),
        order='order:N',
        tooltip=['volume', 'name']
    ).properties(
        width=450,
        height=800
    ).add_selection(
        alt.selection_single()
    ).interactive()

    pshort = alt.Chart(
        source['short'], 
        title=f"{rank_query.instrumentID}空头龙虎榜"
    ).transform_calculate(
        abs_volume = 'abs(datum.volume)'
    ).mark_bar().encode(
        x=alt.X('abs_volume:Q', title=""),
        y=alt.Y('name:N', title="", sort=temp['short']),
        color=alt.Color('type:N', sort=order),
        order='order:N',
        tooltip=['volume', 'name']
    ).properties(
        width=450,
        height=800
    ).add_selection(
        alt.selection_single()
    ).interactive()

    return json.loads(plong.to_json()), json.loads(pshort.to_json())