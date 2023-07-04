from .database import Session
from .models import RankEntry, NetPosition
from .schemas import VolumeType
from . import schemas
from sqlalchemy import select, and_, or_, func

import re

import altair as alt
import numpy as np
import pandas as pd

import json, datetime
from collections import defaultdict
from typing import List



# Return all the entries queried by the user.
def get_rank_entries(db: Session, rank_query: schemas.RankQuery):
    query = (
        select(RankEntry).where(
            and_(
                RankEntry.instrumentID == rank_query.instrumentID,
                RankEntry.date == rank_query.date,
                # RankEntry.exchange == rank_query.exchange,
                or_(
                    RankEntry.volumetype == VolumeType.long,
                    RankEntry.volumetype == VolumeType.short,
                )
            )
        )
        .order_by(RankEntry.rank)
    )
    results= db.execute(query).all()
    entries = [res for (res, ) in results]

    query = (
        select(func.sum(RankEntry.volume), func.sum(RankEntry.change), RankEntry.volumetype).where(
            and_(
                RankEntry.instrumentID == rank_query.instrumentID,
                RankEntry.date == rank_query.date,
                or_(
                    RankEntry.volumetype == VolumeType.long,
                    RankEntry.volumetype == VolumeType.short,
                )
            )
        )
        .group_by(RankEntry.volumetype)
    )
    results= db.execute(query).all()
    volume_sums, change_sums = {}, {}
    for (volume_sum, change_sum, type, ) in results:
        volume_sums[type.value] = volume_sum
        change_sums[type.value] = change_sum

    return entries, volume_sums, change_sums

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


# Draw the bar plots of long volumes and short volumes.
def get_barchart_html(db: Session, rank_query: schemas.RankQuery, target_type: VolumeType):
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

# Calculate net positions for the rank tables.
def get_net_positions_daily(db: Session, net_pos_query: schemas.NetPosDaily):
    query = (
        select(
            RankEntry.companyname, 
            RankEntry.volumetype,
            NetPosition.net_pos
        )
        .where(
            RankEntry.instrumentID == net_pos_query.instrumentID,
            RankEntry.date == net_pos_query.date,
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short
            )
        )
        .join(NetPosition, NetPosition.rank_entry_id == RankEntry.id)
    )

    results= db.execute(query).all()
    long_dict, short_dict = {}, {}

    for (name, type, net_pos, ) in results:
        if type == VolumeType.long:
            long_dict[name] = net_pos
        elif type == VolumeType.short:
            short_dict[name] = net_pos
    
    long_sum = sum(long_dict.values())
    short_sum = sum(short_dict.values())
    return long_dict, short_dict, long_sum, short_sum

# Get all the available company names inside the database.
def get_company_name(db: Session):
    query = (
        select(RankEntry.companyname).distinct().order_by(RankEntry.companyname)
    )
    
    result = db.execute(query).all()
    return [name for (name, ) in result]

    
# Get the json codes for the company-wise line chart.
def get_linechart_company(db: Session, net_pos_query: schemas.NetPosQuery):
    subq = (
        select(func.avg(NetPosition.net_pos).label("net_pos"), RankEntry.date.label("date"))
        .where(
            RankEntry.instrumentType == net_pos_query.instrumentType,
            RankEntry.companyname == net_pos_query.companyName,
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short
            )
        )
        .group_by(RankEntry.instrumentID, RankEntry.date)
        .join(NetPosition, NetPosition.rank_entry_id == RankEntry.id)
        .subquery()
    )

    query = (
        select(func.sum(subq.c.net_pos), subq.c.date)
        .group_by(subq.c.date)
    )
    
    result = db.execute(query).all()

    net_pos_list, date_list = [], []
    for (sum, date, ) in result:
        net_pos_list.append(sum)
        date_list.append(date)


    # Draw the line chart.
    source = pd.DataFrame({
        'date': date_list,
        'net_pos': net_pos_list,
    })
    source['date'] = pd.to_datetime(source['date'])

    plot = alt.Chart(source).mark_line().encode(
        alt.X('date:T', axis=alt.Axis(format="%Y-%m-%d")),
        alt.Y('net_pos:Q'),
        tooltip=['date', 'net_pos'],
    ).properties(
        width=800,
        height=200
    ).add_selection(
        alt.selection_single()
    ).interactive()

    return json.loads(plot.to_json())

# TODO: Get the total sum of net posisions on each date across all companies.
def get_linechart_total(db: Session, selectedType: str):   
    subq = (
        select(func.avg(NetPosition.net_pos).label("net_pos"), RankEntry.date.label("date"))
        .where(
            RankEntry.instrumentType == selectedType,
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short
            )
        )
        .group_by(RankEntry.instrumentID, RankEntry.date, RankEntry.companyname)
        .join(NetPosition, NetPosition.rank_entry_id == RankEntry.id)
        .subquery()
    )

    query = (
        select(func.sum(subq.c.net_pos), subq.c.date)
        .where(subq.c.net_pos >= 0)
        .group_by(subq.c.date)
    )
    
    result = db.execute(query).all()

    for (a,b, ) in result:
        print(a,b)
    # net_pos_list, date_list = [], []
    # for (sum, date, ) in result:
    #     net_pos_list.append(sum)
    #     date_list.append(date)


    # # Draw the line chart.
    # source = pd.DataFrame({
    #     'date': date_list,
    #     'net_pos': net_pos_list,
    # })
    # source['date'] = pd.to_datetime(source['date'])

    # plot = alt.Chart(source).mark_line().encode(
    #     alt.X('date:T', axis=alt.Axis(format="%Y-%m-%d")),
    #     alt.Y('net_pos:Q'),
    #     tooltip=['date', 'net_pos'],
    # ).properties(
    #     width=1000,
    #     height=300
    # ).add_selection(
    #     alt.selection_single()
    # ).interactive()

    # return json.loads(plot.to_json())

# Get the net position ranking given instrument type.
def get_net_pos_rank(db: Session, selectedType: str):  
    dateq = (
        select(func.max(RankEntry.date))
        .where(
            RankEntry.instrumentType == selectedType,
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short
            )
        )
    )
    max_date = db.execute(dateq).scalar()

    subq = (
        select(func.avg(NetPosition.net_pos).label("net_pos"), RankEntry.companyname.label("name"))
        .where(
            RankEntry.instrumentType == selectedType,
            RankEntry.date == max_date,
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short
            )
        )
        .group_by(RankEntry.instrumentID, RankEntry.companyname)
        .join(NetPosition, NetPosition.rank_entry_id == RankEntry.id)
        .subquery()
    )

    subsubq = (
        select(func.sum(subq.c.net_pos).label("net_pos"), subq.c.name)
        .group_by(subq.c.name)
        .subquery()
    )

    long_query = (
        select(subsubq.c.net_pos, subsubq.c.name)
        .where(subsubq.c.net_pos > 0)
        .order_by(subsubq.c.net_pos.desc())
    )

    short_query = (
        select(func.abs(subsubq.c.net_pos), subsubq.c.name)
        .where(subsubq.c.net_pos < 0)
        .order_by(func.abs(subsubq.c.net_pos).desc())
    )
    
    long_result, short_result = db.execute(long_query).all(), db.execute(short_query).all()

    long_list, short_list = [], []
    for (sum, name, ) in long_result:
        long_list.append((name, sum))
    for (sum, name, ) in short_result:
        short_list.append((name, sum))

    return long_list, short_list






    
