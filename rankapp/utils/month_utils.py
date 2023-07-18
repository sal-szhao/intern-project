from ..database import Session
from ..models import MonthMarketInfo
from ..constant import *
from .. import schemas
from sqlalchemy import select, and_, or_, func


def _get_year_range(db: Session, selectedType: str):
    '''
    Helper function for getting the year range for a selected contract type.
    '''
    query = (select(func.max(MonthMarketInfo.date), func.min(MonthMarketInfo.date))
            .where(MonthMarketInfo.contractType == selectedType)
            )
    max, min = db.execute(query).all()[0]
    return max.year, min.year


def get_increase_percentage(db: Session, month_query: schemas.MonthQuery):
    '''
    Get monthly increase / decrease percentage of a specific contract.
    '''
    max_year, min_year = _get_year_range(db, month_query.contractType)
    selectedIDs = [month_query.contractType + str(year)[2:] + month_query.contractMonth for year in range(min_year, max_year + 1)]

    query = (
        select(MonthMarketInfo.close, MonthMarketInfo.date)
        .where(MonthMarketInfo.contractID.in_(selectedIDs))
        .order_by(MonthMarketInfo.date)
    )

    result = db.execute(query).all()
    
    table_dict = {}
    prev_close = None
    for (close, date, ) in result:
        if prev_close and date.year not in table_dict.keys():
            table_dict[date.year] = {}
        
        if prev_close:
            table_dict[date.year][date.month] = (close - prev_close) / prev_close * 100
            table_dict[date.year][0] = date.year
        
        prev_close = close
    
    title_dict = {}
    title_dict[0] = "年份"
    for i in range(1, 13):
        title_dict[i] = MONTH_TRANS[i]
    table_list = [title_dict]
    for year in table_dict.keys():
        table_list.append(table_dict[year])

    return table_list