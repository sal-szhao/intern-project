from ..database import Session
from ..models import RankEntry, NetPosition, MarketInfo
from ..constant import *
from .. import schemas
from sqlalchemy import select, and_, or_, func
import datetime


def get_prod_pos(db: Session, selectedType: str):
    '''
    Get the total number of open interests(positions) of a specific product type.
    Return day-wise and season-wise line plot.
    '''

    query = (
        select(func.sum(MarketInfo.interest), MarketInfo.date)
        .where(MarketInfo.contractType == selectedType)
        .group_by(MarketInfo.date)  
    )

    result = db.execute(query).all()

    line_day_list, line_season_list, line_season_dict = [], [], {}
    for sum, date, in result:
        line_day_list.append({"date": date, "value": sum})
        
        if date.year not in line_season_dict.keys():
            line_season_dict[date.year] = [{"date": date.strftime("%m-%d"), "value": sum}]
        else:
            line_season_dict[date.year].append({"date": date.strftime("%m-%d"), "value": sum})

    for year in line_season_dict.keys():
        line_season_list.append({"name": year, "list": line_season_dict[year]})

    day_plot = {"title": f"{INS_TYPE_TRANS[selectedType]}商品持仓走势图", "data": line_day_list}
    season_plot = {"title": f"{INS_TYPE_TRANS[selectedType]}商品持仓季节图", "data": line_season_list}

    return day_plot, season_plot



def get_prod_value(db: Session, selectedType: str):
    '''
    Get the total market value of a specific product type.
    Return day-wise and season-wise line plot.
    '''

    query = (
        select(func.sum(MarketInfo.settle * MarketInfo.interest), MarketInfo.date)
        .where(MarketInfo.contractType == selectedType)
        .group_by(MarketInfo.date)  
    )

    result = db.execute(query).all()

    line_day_list, line_season_list, line_season_dict = [], [], {}
    for sum, date, in result:
        sum *= CONTRACT_UNIT[selectedType]
        line_day_list.append({"date": date, "value": sum})

        if date.year not in line_season_dict.keys():
            line_season_dict[date.year] = [{"date": date.strftime("%m-%d"), "value": sum}]
        else:
            line_season_dict[date.year].append({"date": date.strftime("%m-%d"), "value": sum})

    for year in line_season_dict.keys():
        line_season_list.append({"name": year, "list": line_season_dict[year]})

    day_plot = {"title": f"{INS_TYPE_TRANS[selectedType]}商品市值走势图", "data": line_day_list}
    season_plot = {"title": f"{INS_TYPE_TRANS[selectedType]}商品市值季节图", "data": line_season_list}

    return day_plot, season_plot