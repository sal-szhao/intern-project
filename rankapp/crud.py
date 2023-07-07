from .database import Session
from .models import RankEntry, NetPosition
from .constant import *
from . import schemas
from sqlalchemy import select, and_, or_, func

import re
import altair as alt
import pandas as pd
import json, datetime
from collections import defaultdict
from typing import List



# Get all the abbreviations of the contract types.
def get_contract_type(db: Session):
    query = (select(RankEntry.contractType, RankEntry.contractTypeC).distinct())
    result = db.execute(query).all()
    res_list = []
    for (contractType, contractTypeC, ) in result:
        res_list.append({"e_name": contractType, "c_name": contractTypeC})
    return res_list

# Get all contract IDs from the selected abbreviation.
def get_contract_id(db: Session, selected_type: str):
    query = (
        select(RankEntry.contractID)
        .distinct()
        .where(RankEntry.contractType == selected_type)
    )
    result = db.execute(query).all()
    return [id for (id, ) in result]

# Get all the available company names inside the database.
def get_company_name(db: Session):
    query = (select(RankEntry.company).distinct().order_by(RankEntry.company))
    result = db.execute(query).all()
    return [company for (company, ) in result]

# Get all the available dates inside the database.
def get_dates(db: Session):
    query = (select(RankEntry.date).distinct())
    result = db.execute(query).all()
    return [date for (date, ) in result]


# Return the json formats for bar plots of long volumes and short volumes.
def get_barchart_html(db: Session, rank_query: schemas.RankQuery):
    query = (
        select(RankEntry.company, RankEntry.vol, RankEntry.chg, RankEntry.volType)
        .where(
            and_(
                RankEntry.contractID == rank_query.contractID,
                RankEntry.date == rank_query.date,
            )
        )
        .order_by(RankEntry.rank)
    )   
    result = db.execute(query).all()

    volume_long, type_long, name_long = [], [], []
    volume_short, type_short, name_short = [], [], []
    pure_long, pure_short = [], []

    for (company, vol, chg, volType, ) in result:
        if volType == 'b':
            volume_long.append(vol)
            type_long.append('多头')
            name_long.append(company)

            volume_long.append(chg)
            name_long.append(company)
            if chg >= 0:
                type_long.append("增加")
            else:
                type_long.append("减少")

            pure_long.append(company)
        elif volType == 's':
            volume_short.append(vol)
            type_short.append('空头')
            name_short.append(company)

            volume_short.append(chg)
            name_short.append(company)
            if chg >= 0:
                type_short.append("增加")
            else:
                type_short.append("减少")

            pure_short.append(company)

    bar_chart_long = _draw_bar_chart(volume_long, name_long, type_long, \
                                      pure_long, rank_query.contractID, 'b')
    bar_chart_short = _draw_bar_chart(volume_short, name_short, type_short, \
                                      pure_short, rank_query.contractID, 's')

    return bar_chart_long, bar_chart_short


# Get the json codes for the company-wise line chart.
def get_linechart_company(db: Session, net_pos_query: schemas.NetPosQuery):
    subq = (
        select(func.avg(NetPosition.net).label("net"), RankEntry.date)
        .where(
            RankEntry.contractType == net_pos_query.contractType,
            RankEntry.company == net_pos_query.company,
        )
        .group_by(RankEntry.contractID, RankEntry.date)
        .join(NetPosition, NetPosition.rank_id == RankEntry.id)
        .subquery()
    )

    query = (
        select(func.sum(subq.c.net), subq.c.date)
        .group_by(subq.c.date)
    )
    
    result = db.execute(query).all()

    res_dict = {}
    for (sum, date, ) in result:
        res_dict[date] = sum

    # If there is no data for the company at certain dates, use 0 by default.
    date_list = get_dates(db)
    for date in date_list:
        if date not in res_dict.keys():
            res_dict[date] = 0

    line_chart_company = _draw_line_chart(res_dict.keys(), res_dict.values())
    return line_chart_company

# Get the total sum of net posisions on each date across all companies.
def get_linechart_total(db: Session, selectedType: str):   
    subq = (
        select(
            func.avg(NetPosition.net).label("net"),
            RankEntry.company,
            RankEntry.date,
        )  
        .where(RankEntry.contractType == selectedType)
        .group_by(RankEntry.contractID, RankEntry.date, RankEntry.company)
        .join(NetPosition, NetPosition.rank_id == RankEntry.id)
        .subquery()
    )

    subsubq = (
        select(func.sum(subq.c.net).label("net"), subq.c.company, subq.c.date)
        .group_by(subq.c.company, subq.c.date)
        .subquery()
    )

    long_query = (
        select(func.sum(subsubq.c.net), subsubq.c.date)
        .where(subsubq.c.net > 0)
        .group_by(subsubq.c.date)
    )

    short_query = (
        select(func.sum(subsubq.c.net), subsubq.c.date)
        .where(subsubq.c.net < 0)
        .group_by(subsubq.c.date)
    )
    
    long_result, short_result = db.execute(long_query).all(), db.execute(short_query).all()

    sum_list, date_list, type_list = [], [], []
    for (sum, date, ) in long_result:
        sum_list.append(sum)
        date_list.append(date)
        type_list.append('long')
    for (sum, date, ) in short_result:
        sum_list.append(-sum)
        date_list.append(date)
        type_list.append('short')

    line_chart_total = _draw_line_chart(date_list, sum_list, type_list)
    return line_chart_total



def get_rank_entries(db: Session, rank_query: schemas.RankQuery, volType: str):
    '''
    Get all the rank entries queried by the user.
    '''
    query = (
        select(RankEntry, NetPosition.net)
        .where(
            RankEntry.contractID == rank_query.contractID,
            RankEntry.date == rank_query.date,
            RankEntry.volType == volType,
        )
        .order_by(RankEntry.rank)
        .join(NetPosition, NetPosition.rank_id == RankEntry.id)
    )
    results= db.execute(query).all()

    table_dict = {}
    table_dict['title'] = f'{rank_query.contractID}' + f'{VOL_TYPE_TRANS[volType]}' + '龙虎榜'

    table_dict['header'] = []
    header_list = ['席位', '持仓', '增减', '净持仓']
    for i, header in enumerate(header_list):
        table_dict['header'].append({'id': i, 'cn_name': header})

    table_dict['list'] = []
    sum_vol, sum_chg, sum_net = 0, 0, 0
    for (entry, net, ) in results:
        sum_vol += entry.vol
        sum_chg += entry.chg
        sum_net += net

        entry_dict = {0: entry.company, 1: entry.vol, 2: entry.chg, 3: net}
        table_dict['list'].append(entry_dict)
    sum_dict = {0: '合计：', 1: sum_vol, 2: sum_chg, 3: sum_net}
    table_dict['list'].append(sum_dict)

    return table_dict

# Get the net position ranking given contract type.
def get_net_rank(db: Session, selectedType: str):  
    dateq = (select(func.max(RankEntry.date)).where(RankEntry.contractType == selectedType))
    max_date = db.execute(dateq).scalar()

    subq = (
        select(func.avg(NetPosition.net).label("net"), RankEntry.company)
        .where(
            RankEntry.contractType == selectedType,
            RankEntry.date == max_date,
        )
        .group_by(RankEntry.contractID, RankEntry.company)
        .join(NetPosition, NetPosition.rank_id == RankEntry.id)
        .subquery()
    )

    subsubq = (
        select(func.sum(subq.c.net).label("net"), subq.c.company)
        .group_by(subq.c.company)
        .subquery()
    )

    long_query = (
        select(subsubq.c.net, subsubq.c.company)
        .where(subsubq.c.net > 0)
        .order_by(subsubq.c.net.desc())
    )

    short_query = (
        select(func.abs(subsubq.c.net), subsubq.c.company)
        .where(subsubq.c.net < 0)
        .order_by(func.abs(subsubq.c.net).desc())
    )
    
    long_result, short_result = db.execute(long_query).all(), db.execute(short_query).all()

    long_list, short_list = [], []
    long_sum, short_sum = 0, 0
    for (sum, name, ) in long_result:
        long_list.append((name, sum))
        long_sum += sum
    for (sum, name, ) in short_result:
        short_list.append((name, sum))
        short_sum += sum

    res_dict = {}
    res_dict['b'] = (long_list, long_sum)
    res_dict['s'] = (short_list, short_sum)
    return res_dict






    
