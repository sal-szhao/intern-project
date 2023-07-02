import re
import datetime, time

from driver import driver
from selenium.webdriver.common.by import By

from rankapp.database import Session, engine, mapper_registry
from rankapp.models import RankEntry

from sqlalchemy import select

# Create all the tables.
with engine.begin() as connection:
    if 'rank_entry' not in mapper_registry.metadata.tables:
        mapper_registry.metadata.create_all(connection)
    else:
        print('table rank_entry already exists')

# Start scraping data. (June)
driver.get('http://www.cffex.com.cn/ccpm/')

base = datetime.datetime.today()
numdays = 30
date_list = [(base - datetime.timedelta(days=x)).strftime("%Y-%m-%d") for x in range(numdays)][::-1]

volumetype_list = ['trading', 'long', 'short']

# session = Session()

date_input = driver.find_element(By.ID, "actualDate")
query_btn = driver.find_element(By.CLASS_NAME, "btn-query")
instrument_select_list = driver.find_elements(By.CSS_SELECTOR, "#selectSec option")

rank_insert_list = []               # List of class objects to insert at once.

for date in date_list:
    print(date)

    # Operate buttons and inputs to demonstrate different data.
    date_input.clear()
    date_input.send_keys(date)
    time.sleep(0.01)

    for instrument_select in instrument_select_list:
        # print(instrument_select.text)
        instrument_select.click()
        query_btn.click()
        time.sleep(0.1)

        # Iterate through all the instrumentIDs in the page.
        instrument_IDs = driver.find_elements(By.CSS_SELECTOR, ".IF_first a")
        for i in range(len(instrument_IDs)):
            # Get data in the table.
            prefix = f".ifright div:nth-of-type({2*i+3}) tr:not(:last-child) "
            rank = driver.find_elements(By.CSS_SELECTOR, prefix + ".if-listf")
            company_name = driver.find_elements(By.CSS_SELECTOR, prefix + ".if-listg")
            vol = driver.find_elements(By.CSS_SELECTOR, prefix + ".if-listh")
            chg = driver.find_elements(By.CSS_SELECTOR, prefix + ".if-listi")

            # Check if there is any missing data.
            assert len(rank) == len(company_name) == len(vol) == len(chg), 'There is missing data.'

            # Create a list of class objects for later insertions.
            for j in range(len(rank)):
                rank2insert = RankEntry(
                    companyname = company_name[j].text, 
                    instrumentType = instrument_select.text,
                    instrumentID = re.findall(r'合约:(.*)', instrument_IDs[i].text)[0],
                    exchange = "CFFEX",
                    rank = int(rank[j].text),
                    change = int(chg[j].text),
                    date = datetime.datetime.strptime(date, '%Y-%m-%d'),
                    volume = int(vol[j].text),
                    volumetype = volumetype_list[j % 3]
                )
                rank_insert_list.append(rank2insert)

with Session.begin() as session:
    session.add_all(rank_insert_list)
        
    # time.sleep(0.5)
    # with Session.begin() as session:
    #     result = session.execute(select(RankEntry).filter_by(rank=1)).all()
    #     for row in result:
    #         print(row)

# https://matplotlib.org/stable/gallery/user_interfaces/web_application_server_sgskip.html

