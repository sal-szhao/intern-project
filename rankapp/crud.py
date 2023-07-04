from .database import Session
from .models import RankEntry
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

# TODO: Draw the line plot of the volumes vs. dates of a specific instrument.
def get_linechart_html(db: Session, rank_query: schemas.RankQuery):
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

# Calculate net positions from rank tables and return a dictionary.
def get_net_positions_daily(db: Session, net_pos_query: schemas.NetPosDaily):
    query = (
        select(
            RankEntry.companyname, 
            RankEntry.volume,
            RankEntry.volumetype
        )
        .where(
            RankEntry.instrumentID == net_pos_query.instrumentID,
            RankEntry.date == net_pos_query.date,
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short
            )
        )
    )

    results= db.execute(query).all()
    long_dict, short_dict = defaultdict(lambda: 0), defaultdict(lambda: 0)
    res_dict = {}
    long_names, short_names = [], []

    for (name, volume, type, ) in results:
        if type == VolumeType.long:
            long_dict[name] = volume
            long_names.append(name)
        elif type == VolumeType.short:
            short_dict[name] = volume
            short_names.append(name)
            
    sums = {}
    sums['long'], sums['short'] = 0, 0
    
    for name in long_names:
        res_dict[name] = long_dict[name] - short_dict[name]
        sums['long'] += res_dict[name]
    for name in short_names:
        if name not in res_dict.keys():
            res_dict[name] = long_dict[name] - short_dict[name]
        sums['short'] += res_dict[name]
    
    return res_dict, sums

# Get all the available company names inside the database.
def get_company_name(db: Session):
    query = (
        select(RankEntry.companyname).distinct().order_by(RankEntry.companyname)
    )
    
    result = db.execute(query).all()
    return [name for (name, ) in result]

# Return the net positions list for a selected company and instrument type, as well as corresponding date list.
def get_net_positions(db: Session, net_pos_query: schemas.NetPosQuery):
    # Get the available dates.
    datequery = (
        select(RankEntry.date).distinct()
        .where(
            RankEntry.instrumentType == net_pos_query.instrumentType,
            RankEntry.companyname == net_pos_query.companyName,
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short
            )
        )
    )
    date_result = db.execute(datequery).all()
    date_list = [date for (date, ) in date_result]

    instrument_ids = get_instrument_id(db, net_pos_query.instrumentType)

    # Get the net positions on each date.
    net_pos_list = []
    for date in date_list:
        curr_vol = 0
        for instrument_id in instrument_ids:
            net_pos_daily = schemas.NetPosDaily(instrumentID=instrument_id, date=date)
            net_dict, _ = get_net_positions_daily(db, net_pos_daily)

            if net_pos_query.companyName in net_dict:
                curr_vol += net_dict[net_pos_query.companyName]

        net_pos_list.append(curr_vol)

    return date_list, net_pos_list
    
# Get the json codes for the company-wise line chart.
def get_linechart_company(db: Session, net_pos_query: schemas.NetPosQuery):    
    date_list, net_pos_list = get_net_positions(db, net_pos_query)
    
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
        width=1000,
        height=300
    ).add_selection(
        alt.selection_single()
    ).interactive()

    return json.loads(plot.to_json())

# Get the net position ranking given instrument type.
def get_net_pos_rank(db: Session, selectedType: str):   
    datequery = (
        select(func.max(RankEntry.date)).distinct()
        .where(
            RankEntry.instrumentType == selectedType,
            or_(
                RankEntry.volumetype == VolumeType.long,
                RankEntry.volumetype == VolumeType.short
            )
        )
    )
    date_max = db.execute(datequery).scalar()

    company_name_list = get_company_name(db)
    for company_name in company_name_list:
        net_pos_daily = schemas.NetPosDaily(instrumentID=instrument_id, date=date)
            net_dict, _ = get_net_positions_daily(db, net_pos_daily)

# Get the total sum of net posisions on each date across all companies.
# def get_linechart_total(db: Session, selectedType: str):   
#     long_list, short_list = defaultdict(lambda: 0), defaultdict(lambda: 0) 
#     company_name_list = get_company_name(db)
#     for company_name in company_name_list:
#         curr_query = schemas.NetPosQuery(instrumentType=selectedType, companyName=company_name)
#         date_list, net_pos_list = get_net_positions(db, curr_query)
#         for i, date in enumerate(date_list):
#             if net_pos_list[i] >= 0:
#                 long_list[date] += net_pos_list[i]
#             else:
#                 short_list[date] += net_pos_list[i]

#     # Draw the line chart.
#     source = pd.DataFrame({
#         'date': long_list.keys(),
#         'net_pos': long_list.values(),
#     })
#     source['date'] = pd.to_datetime(source['date'])

#     plot = alt.Chart(source).mark_line().encode(
#         alt.X('date:T', axis=alt.Axis(format="%Y-%m-%d")),
#         alt.Y('net_pos:Q'),
#         tooltip=['date', 'net_pos'],
#     ).properties(
#         width=1000,
#         height=300
#     ).add_selection(
#         alt.selection_single()
#     ).interactive()

#     return json.loads(plot.to_json())




    
