import click
import datetime as dt
from datetime import datetime
from bsv.downloader_mi import *
from rankapp.database import Session, engine, mapper_registry
from rankapp.models import MarketInfo

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
def get_market_info(start_date, end_date, exchange):
    with engine.begin() as connection:
            mapper_registry.metadata.create_all(connection)

    session = Session()
    
    # mi_{exchange} returns a tuple like:
    # ('20230703', 'SHFE', 'sp', '纸浆', 'sp2311', 68080.8, 67750.8, 67800.8, 
    # 67520.8, 67610.8, 67670.8, 48163, 1629707.43, 103362)
    _func = globals()['_'.join(['mi', exchange.lower()])]
    while start_date <= end_date:
        market_insert_list = []
        for i in _func(start_date):
            date, ex, contractType, contractTypeC, contractID, settle_prev, \
            open, high, low, close, settle, vol, turnover, interest = i

            market2insert = MarketInfo(
                        date = datetime.strptime(date, '%Y%m%d').date(),
                        ex = ex,
                        contractType = contractType,
                        contractTypeC = contractTypeC,
                        contractID = contractID.lower(),
                        settle_prev = settle_prev,
                        open = open,
                        high = high,
                        low = low,
                        close = close,
                        settle = settle,
                        vol = vol,
                        turnover = turnover,
                        interest = interest,
                    )
            market_insert_list.append(market2insert)

        session.add_all(market_insert_list)
        start_date = get_next_date(start_date)

    session.commit()  
    session.close()

if __name__ == '__main__':
    main()