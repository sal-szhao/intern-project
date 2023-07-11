from ..database import Session
from ..models import RankEntry, NetPosition, MarketInfo
from ..constant import *
from .. import schemas
from sqlalchemy import select, and_, or_, func
import datetime


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
   
    return {"name": "席位净持仓", "list": line_list}


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
        "namez": "纯总净持仓", 
        "data": [
            {"name": "多头", "list": long_list},
            {"name": "空头", "list": short_list},
        ]
    }

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
    if result:
        return abs(result)
    else:
        return 0


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


def get_k_linechart_net(db: Session, selectedType: str):  
    '''
    Get the data necessary to draw the k line plot of the contract type.
    ''' 
    # Decide which contract is the main contract.
    query = (
        select(
            func.max(MarketInfo.interest), 
            MarketInfo.date, 
            MarketInfo.open, 
            MarketInfo.close, 
            MarketInfo.low, 
            MarketInfo.high
        )
        .where(
            MarketInfo.contractType == selectedType,
        )
        .group_by(MarketInfo.date)
    )

    line_list = []
    result = db.execute(query).all()
    for _, date, open, close, low, high in result:
        line_list.append({
            "date": date, 
            "open": open,
            "close": close,
            "low": low,
            "high": high,
        })
    
    return {"name": "主连合约", "list": line_list}