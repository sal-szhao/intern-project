from .database import Session
from .models import RankEntry, NetPosition
from .constant import *
from . import schemas
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import aliased
from pypinyin import lazy_pinyin, Style


import re
import altair as alt
import pandas as pd
import json, datetime
from collections import defaultdict
from typing import List



def get_contract_type(db: Session):
    '''
    Get all the abbreviations of the contract types.
    '''
    query = (select(RankEntry.contractType, RankEntry.contractTypeC).distinct())
    result = db.execute(query).all()
    res_list = []
    for (contractType, contractTypeC, ) in result:
        res_list.append({"e_name": contractType, "c_name": contractTypeC})
    return res_list

def get_contract_id(db: Session, selected_type: str):
    '''
    Get all contract IDs from the selected abbreviation.
    '''
    query = (
        select(RankEntry.contractID)
        .distinct()
        .where(RankEntry.contractType == selected_type)
    )
    result = db.execute(query).all()
    return [id for (id, ) in result]

def get_date(db: Session, selected_id: str):
    '''
    Get the availabe date range for the contract.
    '''
    query = (
        select(
            func.min(RankEntry.date),
            func.max(RankEntry.date),
        )
        .where(RankEntry.contractID == selected_id)
    )
    start_date, end_date = db.execute(query).one()
    return {"start_date": start_date, "end_date": end_date}

def get_company(db: Session):
    '''
    Get all the available company names inside the database.
    '''
    query = (select(RankEntry.company).distinct())
    result = db.execute(query).all()
    company_list = [company for (company, ) in result]    
    company_list.sort(key=lambda keys:[lazy_pinyin(i, style=Style.TONE3) for i in keys])
    return company_list


def get_barchart_rank(db: Session, rank_query: schemas.RankQuery, volType: str):
    '''
    Return the data necessary to draw the bar plot.
    f_order: 0 for positions, 1 for increase, -1 for decrease.
    '''
    query = (
        select(RankEntry.company, RankEntry.vol, RankEntry.chg, RankEntry.volType)
        .where(
            and_(
                RankEntry.contractID == rank_query.contractID,
                RankEntry.date == rank_query.date,
                RankEntry.volType == volType,
            )
        )
        .order_by(RankEntry.rank)
    )   

    result = db.execute(query).all()

    bar_list = []
    for (company, vol, chg, volType, ) in result:
        bar_list.append({"f_label": company, "f_value": vol, "f_order": 0})
        if chg > 0:
            bar_list.append({"f_label": company, "f_value": chg, "f_order": 1})
        elif chg < 0:
            bar_list.append({"f_label": company, "f_value": chg, "f_order": -1})
    bar_chart = {"title": f'{rank_query.contractID}' + f'{VOL_TYPE_TRANS[volType]}' + '龙虎榜', "list": bar_list}

    return bar_chart


def _get_date_all(db: Session):
    '''
    Get all the available dates inside the database.
    '''
    query = (select(RankEntry.date).distinct().order_by(RankEntry.date))
    result = db.execute(query).all()
    return [date for (date, ) in result]

def get_linechart_net_company(db: Session, net_pos_query: schemas.NetPosQuery):
    '''
    Get the data necessary to draw the company line plot in the net page.
    '''
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

    line_list = []
    date_check = []
    for (sum, date, ) in result:
        date_check.append(date)
        line_list.append({"date": date, "value": sum, "order": int(sum >= 0)})

    date_all = _get_date_all(db=db)
    date_miss = set(date_all) - set(date_check)

    for date in date_miss:
        line_list.append({"date": date, "value": 0, "order": 1})
   
    return {"title": "席位净持仓", "list": line_list}


def get_linechart_net_total(db: Session, selectedType: str):  
    '''
    Get the data necessary to draw the total line plot in the net page.
    ''' 
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

    long_list, short_list = [], []
    for (sum, date, ) in long_result:
        long_list.append({"date": date, "value": sum})
    for (sum, date, ) in short_result:
        short_list.append({"date": date, "value": -sum})

    return {
        "title": "纯总净持仓", 
        "data": [
            {"name": "多头", "list": long_list},
            {"name": "空头", "list": short_list},
        ]
    }


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


def _get_prev_net(db: Session, net_pos_query: schemas.NetPosQuery, selectedDate: datetime.date):
    '''
    Get the net position on the previous date given company, date, contract type.
    '''
    subq = (
        select(func.avg(NetPosition.net).label("net"), RankEntry.contractID)
        .where(
            RankEntry.contractType == net_pos_query.contractType,
            RankEntry.date == selectedDate,
            RankEntry.company == net_pos_query.company,
        )
        .group_by(RankEntry.contractID)
        .join(NetPosition, NetPosition.rank_id == RankEntry.id)
        .subquery()
    )
    query = (select(func.sum(subq.c.net)))
    result = db.execute(query).scalar()
    return abs(result)


def get_net_rank(db: Session, selectedType: str, volType: str):  
    '''
    Get the net position ranking given contract type.
    '''
    date_all = _get_date_all(db=db)
    curr_date, prev_date = date_all[-1], date_all[-2]

    subq = (
        select(func.avg(NetPosition.net).label("net"), RankEntry.company)
        .where(
            RankEntry.contractType == selectedType,
            RankEntry.date == curr_date,
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

    filter_dict = {"b": 1, "s": -1}
    query = (
        select(func.abs(subsubq.c.net), subsubq.c.company)
        .where(subsubq.c.net * filter_dict[volType] > 0)
        .order_by(func.abs(subsubq.c.net).desc())
    )
    
    result = db.execute(query).all()


    table_list = []
    net_total, chg_total = 0, 0
    for (net, name, ) in result:
        net_pos_query = schemas.NetPosQuery(contractType=selectedType, company=name)
        prev_net = _get_prev_net(db=db, net_pos_query=net_pos_query, selectedDate=prev_date)
        change = net - prev_net
        net_total += net
        chg_total += change
        table_list.append({0: name, 1: net, 2: change})

    table_list.append({0: "合计：", 1: net_total, 2: chg_total})
    
    table_dict = {}
    table_dict['title'] = f"净{VOL_TYPE_TRANS[volType][0]}席位排行"
    table_dict['header'] = []
    header_list = ["席位", f"净{VOL_TYPE_TRANS[volType][0]}持仓", "增减"]
    for i, header in enumerate(header_list):
        table_dict['header'].append({'id': i, 'cn_name': header})

    table_dict["data"] = table_list

    return table_dict






    
