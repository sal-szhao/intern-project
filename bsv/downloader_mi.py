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

from .constant import (SHFE_URL_MI, SHFE_C2P,
                       CFFEX_INIT, CFFEX_URL_MI, CFFEX_C2P,
                       CZCE_URL_before_20151008, CZCE_URL, CZCE_URL_before_20100825,
                       CZCE_ALL_C2P, CZCE_cn, CZCE_BEFORE_CHANGE, CZCE_P2C,
                       DCE_URL, DCE_C2P, DCE_URL_HTML)

__all__ = ['mi_shfe', 'mi_cffex']

def _html_from_requests(url, encoding):
    """
    通过requests获取bs4格式文件
    """
    _requests = requests.get(url)
    _requests.encoding = encoding
    _requests = BeautifulSoup(_requests.text, 'lxml')
    return _requests


def mi_shfe(tday):
    """
    上期所解析json格式的原始数据
    """
    _url = SHFE_URL_MI % tday
    r = requests.get(_url, headers={'user-agent': 
                                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'})
    if r.status_code == 200:
        r = r.json()
        for row in r['o_curinstrument']:
            if row['PRODUCTGROUPID'].strip() in ["", "sc_tas"]:
                continue
            if row['DELIVERYMONTH'].strip() in ["小计", "efp"]:
                continue
            # 品种代码： cu
            code = row['PRODUCTGROUPID'].strip()
            # 品种中文： 铜
            product = SHFE_C2P[code]
            # 合约: cu1805
            contract = row['PRODUCTGROUPID'].strip() + row['DELIVERYMONTH'].strip()  
            # 前结算
            settle_prev = row['PRESETTLEMENTPRICE']
            # 今开盘
            open = row['OPENPRICE']
            # 最高价
            high = row['HIGHESTPRICE']
            # 最低价	
            low = row['LOWESTPRICE']
            # 收盘价
            close = row['CLOSEPRICE']
            # 结算参考价
            settle = row['SETTLEMENTPRICE']
            # 成交手
            volume = row['VOLUME']
            # 成交额
            turnover = row['TURNOVER']
            # 持仓手
            openinterest = row['OPENINTEREST']

            _market_info = [tday, "SHFE", code, product, contract, settle_prev, open, high, \
                            low, close, settle, volume, turnover, openinterest]
            for i in range(len(_market_info)):
                if not _market_info[i]:
                    _market_info[i] = 0
            _market_info = tuple(_market_info)

            yield _market_info


def mi_cffex(tday):
    """
    cffex的品种成交持仓排名在各自网页中，如果cffex中增加新品种，则需要在CFFEX_INIT更新
    """
  
    _url = CFFEX_URL_MI % (tday[:-2], tday[-2:])
    r = _html_from_requests(_url, 'utf-8')
    for data in r.select("dailydata"):
        contract = data.instrumentid.get_text().strip().lower()
        if '-' in contract:
            continue
        code = contract[:-4].lower()
        if CFFEX_INIT[code] > tday:  # 若品种上市日期在指定交易日之后，则忽略
            continue
        product = CFFEX_C2P[code]
        settle_prev =  data.presettlementprice.get_text().strip()
        open = data.openprice.get_text().strip()
        high = data.highestprice.get_text().strip()
        low = data.lowestprice.get_text().strip()
        close = data.closeprice.get_text().strip()
        settle = data.settlementprice.get_text().strip()
        volume = data.volume.get_text().strip()
        turnover = data.turnover.get_text().strip()
        turnover = float(turnover) / 10000
        openinterest = data.openinterest.get_text().strip()

        _market_info = (tday, "CFFEX", code, product, contract, settle_prev, open, high, \
                        low, close, settle, volume, turnover, openinterest)
        yield _market_info