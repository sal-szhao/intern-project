import click
import datetime as dt
from datetime import datetime
from bsv.downloader import hp_shfe, hp_cffex
from rankapp.database import Session, engine, mapper_registry
from rankapp.models import RankEntry

def get_next_date(date, timedelta=1, timeformat='%Y%m%d'):
    """
    get the next date by default with the format of string '%Y%m%d'
    """
    next_date = dt.datetime.strptime(date, timeformat) + dt.timedelta(timedelta)
    return next_date.strftime(timeformat)

@click.group()
def main():
    pass

@main.command()
@click.option('--start-date', '-s', default='20230501', help='测试交易日起始日', type=click.STRING)
@click.option('--end-date', '-e', default='20230706', help='测试交易日终止日', type=click.STRING)
@click.option('--exchange', '-x', required=True, help='交易所简称 -- SHFE CFFEX DCE CZCE')
def get_data(start_date, end_date, exchange):
    # Create all the tables.
    with engine.begin() as connection:
        mapper_registry.metadata.create_all(connection)

    session = Session()

    # hp_{exchange} returns a tuple like:
    # ('20230703', 'SHFE', 'sp', '纸浆', 'sp2311', 's', 20, '恒泰期货', 321, 2)
    _func = globals()['_'.join(['hp', exchange.lower()])]
    while start_date <= end_date:
        rank_insert_list = []
        for i in _func(start_date):
            date, ex, contractType, contractTypeC, contractID, \
            volType, rank, company, vol, chg = i 
            
            rank2insert = RankEntry(
                date = datetime.strptime(date, '%Y%m%d').date(),
                ex = ex,
                contractType = contractType,
                contractTypeC = contractTypeC,
                contractID = contractID,
                volType = volType,
                rank = rank,
                company = company,
                vol = vol,
                chg = chg
            )
            rank_insert_list.append(rank2insert)

        session.add_all(rank_insert_list)
        start_date = get_next_date(start_date)

    session.commit()  
    session.close()

if __name__ == '__main__':
    main()