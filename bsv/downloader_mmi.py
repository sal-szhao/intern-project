from bs4 import BeautifulSoup
import chardet
import datetime as dt
import os
import pandas as pd
import re
import requests
import shutil
import time
import zipfile

from .constant import (SHFE_URL_MMI, SHFE_C2P,
                       CFFEX_INIT, CFFEX_URL_MMI, CFFEX_C2P,
                       CZCE_URL_before_20151008, CZCE_URL, CZCE_URL_before_20100825,
                       CZCE_ALL_C2P, CZCE_cn, CZCE_BEFORE_CHANGE, CZCE_P2C,
                       DCE_URL, DCE_C2P, DCE_URL_HTML)

__all__ = ['mmi_shfe', 'mmi_cffex']

def _html_from_requests(url, encoding):
    """
    通过requests获取bs4格式文件
    """
    _requests = requests.get(url)
    _requests.encoding = encoding
    _requests = BeautifulSoup(_requests.text, 'lxml')
    return _requests


def mmi_shfe(tmonth):
    """
    上期所解析json格式的原始数据
    """
    _url = SHFE_URL_MMI % tmonth
    r = requests.get(_url, headers={'user-agent': 
                                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'})
    if r.status_code == 200:
        r = r.json()
        for row in r['o_curtransaction']:
            if not row['CLOSEPRICE']:
                continue
            # 品种代码： cu
            code = row['PRODUCT'].strip()
            # 品种中文： 铜
            product = SHFE_C2P[code]
            # 合约: cu1805
            contract = row['INSTRUMENTID'].strip()
            # 月开盘
            open = row['OPENPRICE']
            # 最高价
            high = row['HIGHESTPRICE']
            # 最低价	
            low = row['LOWESTPRICE']
            # 月收盘价
            close = row['CLOSEPRICE']
            # 月末结算价
            settle = row['SETTLEMENTPRICE']
            # 成交量
            volume = row['VOLUME']
            # 成交额
            turnover = row['TURNOVER']
            # 持仓量
            openinterest = row['OPENINTEREST']

            _market_info = [tmonth, "SHFE", code, product, contract, open, high, \
                            low, close, settle, volume, turnover, openinterest]
            for i in range(len(_market_info)):
                if not _market_info[i]:
                    _market_info[i] = 0
            _market_info = tuple(_market_info)

            yield _market_info

def mmi_cffex(tmonth):
    """
    cffex的品种成交持仓排名在各自网页中，如果cffex中增加新品种，则需要在CFFEX_INIT更新
    """
  
    _url = CFFEX_URL_MMI % tmonth
    r = _html_from_requests(_url, 'utf-8')
    for data in r.select("monthlydata"):
        contract = data.instrumentid.get_text().strip().lower()
        if '-' in contract:
            continue
        code = data.productid.get_text().strip().lower()
        if CFFEX_INIT[code] > tmonth:  # 若品种上市日期在指定交易日之后，则忽略
            continue
        product = CFFEX_C2P[code]
        open = data.openprice.get_text().strip()
        high = data.highestprice.get_text().strip()
        low = data.lowestprice.get_text().strip()
        close = data.closeprice.get_text().strip()
        settle = data.settlementprice.get_text().strip()
        volume = data.volume.get_text().strip()
        turnover = data.turnover.get_text().strip()
        turnover = float(turnover) / 10000
        openinterest = data.openinterest.get_text().strip()

        _market_info = (tmonth, "CFFEX", code, product, contract, open, high, \
                        low, close, settle, volume, turnover, openinterest)
        yield _market_info