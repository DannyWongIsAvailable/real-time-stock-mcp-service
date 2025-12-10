import sys
import os
import time


# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.crawler.base_crawler import EastMoneyBaseSpider

import requests
from typing import Optional, Dict, Any, List
import json
import re


class ValuationDataCrawler(EastMoneyBaseSpider):
    """
    估值数据爬虫类

    用于获取股票的估值相关信息，如市盈率、市净率、股息率等估值指标
    """
    
    VALUATION_TREND_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    VALUATION_PERCENTILE_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    INSTITUTIONAL_RATING_URL = "https://reportapi.eastmoney.com/report/list"
    
    # 指标类型常量
    INDICATOR_TYPE_PE_TTM = 1  # 市盈率TTM
    INDICATOR_TYPE_PB_MRQ = 2  # 市净率MRQ
    INDICATOR_TYPE_PS_TTM = 3  # 市销率TTM
    INDICATOR_TYPE_PC_TTM = 4  # 市现率TTM
    
    # 时间周期常量
    DATE_TYPE_1YEAR = 1   # 1年
    DATE_TYPE_3YEAR = 2   # 3年
    DATE_TYPE_5YEAR = 3   # 5年
    DATE_TYPE_10YEAR = 4  # 10年
    
    # 中文描述映射
    INDICATOR_TYPE_MAP = {
        INDICATOR_TYPE_PE_TTM: "市盈率TTM",
        INDICATOR_TYPE_PB_MRQ: "市净率MRQ",
        INDICATOR_TYPE_PS_TTM: "市销率TTM",
        INDICATOR_TYPE_PC_TTM: "市现率TTM"
    }
    
    STATISTICS_CYCLE_MAP = {
        DATE_TYPE_1YEAR: "1年",
        DATE_TYPE_3YEAR: "3年",
        DATE_TYPE_5YEAR: "5年",
        DATE_TYPE_10YEAR: "10年"
    }

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = 10,
    ):
        """
        初始化估值数据爬虫
        
        :param session: requests.Session 实例
        :param timeout: 请求超时时间
        """
        super().__init__(session, timeout)

    def get_institutional_rating(self, stock_code: str, begin_time: str, end_time: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取机构评级数据
        
        :param stock_code: 股票代码，如688041
        :param begin_time: 开始时间，格式如2025-10-23
        :param end_time: 结束时间，格式如2025-12-07
        :return: 机构评级数据列表
        """
        # 移除股票代码中的交易所后缀（如果存在）
        clean_stock_code = stock_code.split('.')[0] if '.' in stock_code else stock_code
        
        # 更新headers以更接近浏览器行为
        headers = self.headers.copy()
        headers.update({
            "Referer": "https://data.eastmoney.com/",
            "Host": "reportapi.eastmoney.com"
        })
        
        params = {
            "cb": "datatable1167765",
            "pageNo": 1,
            "pageSize": 50,
            "code": clean_stock_code,
            "industryCode": "",
            "industry": "",
            "rating": "",
            "ratingchange": "",
            "beginTime": begin_time,
            "endTime": end_time,
            "fields": "",
            "qType": 0,
            "p": 1,
            "pageNum": 1,
            "pageNumber": 1,
            "_": int(round(time.time() * 1000))
        }
        
        try:
            response = self.session.get(
                self.INSTITUTIONAL_RATING_URL, 
                params=params, 
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 提取JSON数据（去除JSONP包装）
            text = response.text
            match = re.search(r'datatable1167765\((.*)\)', text)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                return data.get("data", [])
            else:
                return []
                
        except Exception as e:
            return [{"error": f"获取机构评级数据出错: {str(e)}"}]

    def get_valuation_analysis(self, stock_code: str, indicator_type: int, date_type: int = 3) -> Optional[Dict[Any, Any]]:
        """
        获取估值分析数据，包括当前值和历史分位数
        
        :param stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH
        :param indicator_type: 指标类型
                              1 - 市盈率TTM
                              2 - 市净率MRQ
                              3 - 市销率TTM
                              4 - 市现率TTM
        :param date_type: 时间周期类型
                         1 - 1年
                         2 - 3年
                         3 - 5年
                         4 - 10年
        :return: 估值分析数据字典，包含：
                 - SECUCODE: 股票代码
                 - TRADE_DATE: 交易日期
                 - INDICATOR_VALUE: 指标当前值
                 - INDICATOR_TYPE: 指标类型
                 - INDICATOR_TYPE_NAME: 指标类型中文名称
                 - DATE_TYPE: 时间周期类型
                 - DATE_TYPE_NAME: 时间周期类型中文名称
                 - STATISTICS_CYCLE: 统计周期
                 - STATISTICS_CYCLE_NAME: 统计周期中文名称
                 - PERCENTILE_THIRTY: 30%历史分位数
                 - PERCENTILE_FIFTY: 50%历史分位数(中位数)
                 - PERCENTILE_SEVENTY: 70%历史分位数
        """
        # 第一个API调用：获取估值指标当前值
        params1 = {
            "reportName": "RPT_CUSTOM_DMSK_TREND",
            "columns": "ALL",
            "quoteColumns": "",
            "filter": f'(SECUCODE="{stock_code}")(INDICATORTYPE={indicator_type})(DATETYPE={date_type})',
            "pageNumber": 1,
            "pageSize": "",
            "sortTypes": "1",
            "sortColumns": "TRADE_DATE",
            "source": "HSF10",
            "client": "PC",
            "v": "06303860776760081"
        }
        
        # 第二个API调用：获取估值指标历史分位数
        params2 = {
            "reportName": "RPT_STOCKVALUATIONTANTILE",
            "columns": "SECUCODE,STATISTICS_CYCLE,INDEX_TYPE,PERCENTILE_THIRTY,PERCENTILE_FIFTY,PERCENTILE_SEVENTY",
            "quoteColumns": "",
            "filter": f'(SECUCODE="{stock_code}")(INDEX_TYPE="{indicator_type}")(STATISTICS_CYCLE="{date_type}")',
            "pageNumber": 1,
            "pageSize": "",
            "sortTypes": "",
            "sortColumns": "",
            "source": "HSF10",
            "client": "PC",
            "v": "023243304260984377"
        }
        
        try:
            # 获取估值指标当前值
            response1 = self._get_json(self.VALUATION_TREND_URL, params1)
            # 检查响应是否成功
            if response1.get("code") != 0 or response1.get("success") is not True or not response1.get("result"):
                # 如果不成功，返回错误信息
                message = response1.get("message", "未知错误")
                return {"error": message}
            
            data1 = response1["result"]["data"]
            # 提取最新的估值指标数据（即data[-1]）中的关键字段
            indicator_data = {}
            if data1:
                latest_data = data1[-1]
                indicator_data = {
                    "SECUCODE": latest_data.get("SECUCODE"),
                    "TRADE_DATE": latest_data.get("TRADE_DATE"),
                    "INDICATOR_VALUE": latest_data.get("INDICATOR_VALUE"),
                    "INDICATOR_TYPE": self.INDICATOR_TYPE_MAP.get(indicator_type, f"未知指标({indicator_type})"),
                }
            
            # 获取历史分位数数据
            response2 = self._get_json(self.VALUATION_PERCENTILE_URL, params2)
            # 检查响应是否成功
            if response2.get("code") != 0 or response2.get("success") is not True or not response2.get("result"):
                # 如果不成功，返回错误信息
                message = response2.get("message", "未知错误")
                return {"error": message}
            
            data2 = response2["result"]["data"]
            # 提取第一条数据的关键字段
            percentile_data = {}
            if data2:
                first_data = data2[0]
                stat_cycle = first_data.get("STATISTICS_CYCLE")
                percentile_data = {
                    "STATISTICS_CYCLE": self.STATISTICS_CYCLE_MAP.get(int(stat_cycle), f"未知周期({stat_cycle})") if stat_cycle else "未知",
                    "PERCENTILE_THIRTY": first_data.get("PERCENTILE_THIRTY"),
                    "PERCENTILE_FIFTY": first_data.get("PERCENTILE_FIFTY"),
                    "PERCENTILE_SEVENTY": first_data.get("PERCENTILE_SEVENTY")
                }
            
            # 合并两个数据
            combined_data = {**indicator_data, **percentile_data}
            return combined_data
            
        except Exception as e:
            return {"error": str(e)}