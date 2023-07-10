from ..database import Session
from ..models import RankEntry, NetPosition
from ..constant import *
from .. import schemas
from sqlalchemy import select, and_, or_, func


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
    table_dict['title'] = f'{INS_TYPE_TRANS[rank_query.contractID[:-4]]}' + f'{rank_query.contractID[-4:]}' + f'{VOL_TYPE_TRANS[volType]}' + '龙虎榜'

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
    bar_chart = {"title": f'{INS_TYPE_TRANS[rank_query.contractID[:-4]]}' + f'{rank_query.contractID[-4:]}' + f'{VOL_TYPE_TRANS[volType]}' + '龙虎榜', "list": bar_list}

    return bar_chart


def get_linechart_rank(db: Session, selectedID: str):
    '''
    Return the data necessary to draw the line plot.
    '''
    query = (
        select(
            func.sum(RankEntry.vol), 
            func.sum(NetPosition.net), 
            RankEntry.date,
            RankEntry.volType,
        )
        .where(
            RankEntry.contractID == selectedID,
        )
        .group_by(RankEntry.date, RankEntry.volType)
        .join(NetPosition, NetPosition.rank_id == RankEntry.id)
    )

    results= db.execute(query).all()

    vol_long, vol_short, net_long, net_short = [], [], [], []
    for (vol_sum , net_sum, date, volType, ) in results:
        if volType == "b":
            vol_long.append({"date": date, "value": vol_sum})
            net_long.append({"date": date, "value": net_sum})
        elif volType == "s":
            vol_short.append({"date": date, "value": vol_sum})
            net_short.append({"date": date, "value": abs(net_sum)})

    line_list = [
        {"name": "多头总持仓", "list": vol_long},
        {"name": "空头总持仓", "list": vol_short},
        {"name": "多头净持仓", "list": net_long},
        {"name": "空头净持仓", "list": net_short},
    ]

    return {"title": f'{INS_TYPE_TRANS[selectedID[:-4]]}' + f'{selectedID[-4:]}' + "多空持仓图", "data": line_list}
