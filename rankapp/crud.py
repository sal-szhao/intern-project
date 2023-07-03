from .database import Session
from .models import RankEntry
from .schemas import VolumeType
from . import schemas
from sqlalchemy import select, and_, or_, func

import re

import altair as alt
import numpy as np
import pandas as pd

import json

# Return all the entries queried by the user.
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

# Get all the abbreviations of the insturment types.
def get_instrument_type(db: Session):
    query = (
        select(RankEntry.instrumentType).distinct()
    )
    
    result = db.execute(query).all()
    return [type for (type, ) in result]

# Get all the instrument IDs from the selected abbreviation.
def get_instrument_id(db: Session, selected_type: str):
    query = (
        select(RankEntry.instrumentID).distinct()
    )
    result = db.execute(query).all()
    
    return [id for (id, ) in result if re.search(f'^{selected_type}[0-9]*$', id)]

# Draw the line plot of the volumes vs. dates of a specific instrument.
def get_linechart_html(db:Session, rank_query: schemas.RankQuery):
    # Select data from the databse.
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
    
    # Process the retrieved data.
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

    # Draw the line chart.
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

# Draw the bar plots of long volumes and short volumes.
def get_barchart_html(db:Session, rank_query: schemas.RankQuery, target_type: VolumeType):
    # Select data from the databse.
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

    # Process the retrieved data.
    result = db.execute(query).all()
    volume_list, type_list, name_list = [], [], []
    pure_list = []

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

        pure_list.append(companyname)

    bar_df = pd.DataFrame({
        'volume': volume_list,
        'type': type_list,
        'name': name_list
    })

    # Assign the order to the type of the volume, determining the order inside the stack.
    order = ['long', 'short', 'increase', 'decrease']
    order_num = list(range(4))
    type_order_dict = dict(zip(order, order_num))
    bar_df['type_order'] = bar_df['type'].apply(lambda x: type_order_dict[x])
    
    # Make altair plot.
    if target_type == VolumeType.long:
        trans = "多头"
    if target_type == VolumeType.short:
        trans = "空头"

    plot = alt.Chart(
        bar_df, 
        title=f"{rank_query.instrumentID}{trans}龙虎榜"
    ).transform_calculate(
        abs_volume = 'abs(datum.volume)'
    ).mark_bar().encode(
        x=alt.X('abs_volume:Q', title="").stack('zero'),
        y=alt.Y('name:N', title="", sort=pure_list),
        color=alt.Color('type:N', sort=order),
        order='order:N',
        tooltip=['volume', 'name']
    ).properties(
        width=500,
        height=700
    ).add_selection(
        alt.selection_single()
    ).interactive()


    # Return the json format of the plot for further vega embedding in jinja template.
    return json.loads(plot.to_json())