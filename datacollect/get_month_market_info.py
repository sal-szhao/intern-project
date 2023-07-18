import click
import datetime as dt
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bsv.downloader_mmi import *
from rankapp.database import Session, engine, mapper_registry
from rankapp.models import MonthMarketInfo

def get_next_month(month, timedelta=1, timeformat='%Y%m'):
    """
    get the next month by default with the format of string '%Y%m%d'
    """
    next_date = dt.datetime.strptime(month, timeformat) + relativedelta(months=timedelta)
    return next_date.strftime(timeformat)

@click.group()
def main():
    pass

@main.command()
@click.option('--start-month', '-s', default='202201', help='测试交易日起始月', type=click.STRING)
@click.option('--end-month', '-e', default='202306', help='测试交易日终止月', type=click.STRING)
@click.option('--exchange', '-x', required=True, help='交易所简称 -- SHFE CFFEX DCE CZCE')
def get_month_market_info(start_month, end_month, exchange):
    with engine.begin() as connection:
            mapper_registry.metadata.create_all(connection)

    session = Session()
    
    # mmi_{exchange} returns a tuple like:
    # ('202307', 'SHFE', 'sp', '纸浆', 'sp2311', 68080.8, 67750.8, 67800.8, 
    # 67610.8, 67670.8, 48163, 1629707.43, 103362)
    _func = globals()['_'.join(['mmi', exchange.lower()])]
    while start_month <= end_month:
        market_insert_list = []
        for i in _func(start_month):
            month, ex, contractType, contractTypeC, contractID, \
            open, high, low, close, settle, vol, turnover, interest = i

            market2insert = MonthMarketInfo(
                        date = datetime.strptime(month, '%Y%m').date(),
                        ex = ex,
                        contractType = contractType,
                        contractTypeC = contractTypeC,
                        contractID = contractID.lower(),
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
        start_month = get_next_month(start_month)

    session.commit()  
    session.close()

if __name__ == '__main__':
    main()