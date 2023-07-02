import re
import datetime, time

from driver import driver
from selenium.webdriver.common.by import By

from rankapp.database import Session, engine, mapper_registry
from rankapp.models import RankEntry

from sqlalchemy import select



# If the table exists, then there is not need to create the tables.
with engine.begin() as connection:
    mapper_registry.metadata.create_all(connection)
    

# Parameter initialization.
driver.get('https://www.shfe.com.cn/statements/dataview.html?paramid=kx')
volumetype_list = ['trading', 'long', 'short']

# Switch to rank page.
rank_btn = driver.find_element(By.ID, "pm")
rank_btn.click()

# Iterate through dates.
# Notice that date_list will keep changing as one is clicked, which is not allowed.
date_list = driver.find_elements(By.CSS_SELECTOR, "#calendar > div > table > tbody > tr .has-data")     
disable_date_cnt = 0
for date_link in date_list:
    if "ui-state-disabled" not in date_link.get_attribute("class"):
        break
    disable_date_cnt += 1
max_date_cnt = len(date_list)

# Start iterating.
rank_insert_list = []
for i in range(disable_date_cnt+2, max_date_cnt):
    date_list = driver.find_elements(By.CSS_SELECTOR, "#calendar > div > table > tbody > tr .has-data")     
    date_link = date_list[i]
    date_link.click()
    time.sleep(0.5)
    curr_date = driver.find_element(By.CSS_SELECTOR, "#datatitle > table > tbody > tr:nth-child(2) > td:nth-child(1)").text
    print(curr_date)

    # Display all the instruments at once.
    all_btn = driver.find_element(By.ID, "li_all")
    all_btn.click()
    time.sleep(0.5)

    row_cnt = len(driver.find_elements(By.CSS_SELECTOR, "#addedtable tbody"))

    isInstrument = False
    instrumentID = None
    for i in range(row_cnt):
        row = driver.find_element(By.CSS_SELECTOR, f"#addedtable > tbody:nth-child({i+1}) > tr")

        if row.get_attribute('class') == 'pinz':
            table_head = driver.find_element(By.CSS_SELECTOR, f"#addedtable > tbody:nth-child({i+1}) > tr > td > div:nth-child(1)").text
            if "商品名称" in table_head:
                isInstrument = False
            else:
                isInstrument = True
                curr_instrumentID = driver.find_element(By.CSS_SELECTOR, f"#addedtable > tbody:nth-child({i+1}) > tr > td > div:nth-child(1) > strong").text
                print(curr_instrumentID)


        if isInstrument and row.get_attribute('class') in ['data11', 'data22']:
            entries = driver.find_elements(By.CSS_SELECTOR, f"#addedtable > tbody:nth-child({i+1}) > tr > td")
            for index, entry in enumerate(entries):
                if not entry.text:
                    continue
                if index % 4 == 0:
                    curr_rank = entry.text
                if index % 4 == 1:
                    curr_company_name = entry.text
                if index % 4 == 2:
                    curr_volume = int(entry.text)
                if index % 4 == 3:
                    curr_change = int(entry.text)
                    curr_volume_type = volumetype_list[index % 3]

                    rank2insert = RankEntry(
                        companyname = curr_company_name, 
                        instrumentType = re.findall(r"[a-zA-Z]*", curr_instrumentID)[0].upper(),
                        instrumentID = curr_instrumentID.upper(),
                        exchange = "SHFE",
                        rank = curr_rank,
                        change = curr_change,
                        date = datetime.datetime.strptime(curr_date, '%Y-%m-%d'),
                        volume = curr_volume,
                        volumetype = curr_volume_type
                    )
                  
                    rank_insert_list.append(rank2insert)

    with Session.begin() as session:
        session.add_all(rank_insert_list)

# time.sleep(0.5)
# with Session.begin() as session:
#     result = session.execute(select(RankEntry).filter_by(rank=1)).all()
#     for row in result:
#         print(row)        
    
print('finished')
# selenium.common.exceptions.StaleElementReferenceException: Message: stale element reference: element is not attached to the page document