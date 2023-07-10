from ..database import Session
from ..models import RankEntry
from ..constant import *
from sqlalchemy import select, and_, or_, func
from pypinyin import lazy_pinyin, Style


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
