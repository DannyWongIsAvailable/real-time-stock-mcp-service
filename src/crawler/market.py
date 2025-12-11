import requests
from typing import Dict, List, Optional
from .base_crawler import EastMoneyBaseSpider

class MarketSpider(EastMoneyBaseSpider):
    """
    市场板块行情爬虫类
    
    用于获取东方财富网的板块行情数据，包括行业板块、概念板块、地域板块等。
    """

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = None,
    ):
        super().__init__(session, timeout)
        self.base_url = "https://push2.eastmoney.com/api/qt/clist/get"
        self.fund_flow_url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
        self.billboard_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"

    def get_plate_quotation(self, plate_type: int = 2, page_size: int = 10) -> List[Dict]:
        """
        获取板块行情数据
        
        :param plate_type: 板块类型参数
            - 1: 地域板块  
            - 2: 行业板块
            - 3: 概念板块
        :param page_size: 返回数据条数，默认为10条
        :return: 板块行情数据列表
        """
        # 构建 fs 参数
        fs_param = f"m:90 t:{plate_type} f:!50"
        
        params = {
            "np": "1",
            "fltt": "1",
            "invt": "2",
            "cb": self._generate_callback(),
            "fs": fs_param,
            "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f20,f8,f104,f105,f128,f140,f141,f207,f208,f209,f136,f222",
            "fid": "f3",
            "pn": "1",
            "pz": str(page_size),
            "po": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "dect": "1",
            "wbp2u": "|0|0|0|web",
            "_": str(self._timestamp_ms())
        }

        response = self._get_jsonp(self.base_url, params)
        
        if response and response.get("data") and response["data"].get("diff"):
            return response["data"]["diff"]
        else:
            return []
    
    def get_plate_fund_flow(self, plate_type: int = 2, page_size: int = 10) -> List[Dict]:
        """
        获取板块资金流今日排行
        
        :param plate_type: 板块类型参数
            - 1: 地域板块  
            - 2: 行业板块
            - 3: 概念板块
        :param page_size: 返回数据条数，默认为10条
        :return: 板块资金流数据列表
        """
        # 构建 fs 参数
        fs_param = f"m:90 t:{plate_type}"
        
        params = {
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "cb": self._generate_callback(),
            "fs": fs_param,
            "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13",
            "fid": "f62",
            "pn": "1",
            "pz": str(page_size),
            "po": "1",
            "ut": "8dec03ba335b81bf4ebdf7b29ec27d15",
            "_": str(self._timestamp_ms())
        }

        response = self._get_jsonp(self.base_url, params)
        
        if response and response.get("data") and response["data"].get("diff"):
            return response["data"]["diff"]
        else:
            return []
    
    def get_historical_fund_flow(self, stock_code: str, limit: int = 10) -> Optional[Dict]:
        """
        获取历史资金流向数据
        
        :param stock_code: 股票代码，数字后带上交易所代码，格式如688041.SH
        :param limit: 返回数据条数，默认为10条
        :return: 包含资金流向历史数据的字典
        """
        secid = self.format_secid(stock_code)
        params = {
            "lmt": str(limit),
            "klt": "101",
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
            "ut": "b2884a393a59ad64002292a3e90d46a5",
            "secid": secid,
            "cb": self._generate_callback(),
            "_": str(self._timestamp_ms())
        }
        
        response = self._get_jsonp(self.fund_flow_url, params)
        
        if response and response.get("data"):
            return response["data"]
        else:
            return None
    
    def get_billboard_data(self, trade_date: str, page_size: int = 10) -> list[dict]:
        """
        获取龙虎榜数据
        
        :param trade_date: 交易日期，格式为 YYYY-MM-DD
        :param page_size: 返回数据条数，默认为10条
        :return: 包含龙虎榜数据或错误信息的字典
        """
        params = {
            "sortColumns": "CHANGE_RATE,TRADE_DATE,SECURITY_CODE",
            "sortTypes": "-1,-1,1",
            "pageSize": str(page_size),
            "pageNumber": "1",
            "reportName": "RPT_DAILYBILLBOARD_DETAILSNEW",
            "columns": "SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,TRADE_DATE,EXPLAIN,CLOSE_PRICE,CHANGE_RATE,"
                      "BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,BILLBOARD_DEAL_AMT,ACCUM_AMOUNT,"
                      "DEAL_NET_RATIO,DEAL_AMOUNT_RATIO,TURNOVERRATE,FREE_MARKET_CAP,EXPLANATION,D1_CLOSE_ADJCHRATE,"
                      "D2_CLOSE_ADJCHRATE,D5_CLOSE_ADJCHRATE,D10_CLOSE_ADJCHRATE,SECURITY_TYPE_CODE",
            "source": "WEB",
            "client": "WEB",
            "callback": self._generate_callback(),
            "_": str(self._timestamp_ms())
        }
        
        if trade_date:
            params["filter"] = f"(TRADE_DATE='{trade_date}')"

        response = self._get_jsonp(self.billboard_url, params)
        
        if response and response.get("result") and response["result"].get("data"):
            return response["result"]["data"]
        elif response:
            return [{"error": response.get("message", "未知错误")}]
        else:
            return [{"error": "网络请求失败"}]
    
    def get_stock_billboard_data(self, stock_code: str, page_size: int = 10) -> list[dict]:
        """
        获取股票历次上榜记录
        
        :param stock_code: 股票代码，数字后带上交易所代码，格式如688041.SH
        :param page_size: 返回数据条数，默认为10条
        :return: 包含龙虎榜历史数据或错误信息的列表
        """
        params = {
            "sortColumns": "TRADE_DATE,TRADE_DATE",
            "sortTypes": "-1,-1",
            "pageSize": page_size,
            "pageNumber": "1",
            "reportName": "RPT_BILLBOARD_PERFORMANCEHIS",
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "callback": self._generate_callback(),
            "_": str(self._timestamp_ms())
        }
        # 移除股票代码后缘
        stock_code = stock_code.split(".")[0]
        if stock_code:
            params["filter"] = f"(SECURITY_CODE=\"{stock_code}\")"

        response = self._get_jsonp(self.billboard_url, params)
        
        if response and response.get("result") and response["result"].get("data"):
            return response["result"]["data"]
        elif response:
            return [{"error": response.get("message", "未知错误")}]
        else:
            return [{"error": "网络请求失败"}]

    def get_market_performance(self, secucode: str) -> Optional[List[Dict]]:
        """
        获取股票市场表现数据
        
        :param secucode: 股票代码，格式如300750.SZ
        :return: 包含市场表现数据的列表
        """
        market_performance_url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
        
        params = {
            "reportName": "RPT_PCF10_MARKETPER",
            "columns": "ALL",
            "quoteColumns": "",
            "pageNumber": "1",
            "pageSize": "4",
            "sortTypes": "-1,1",
            "sortColumns": "TRADE_DATE,TIME_TYPE",
            "source": "HSF10",
            "client": "PC",
            "v": "08484108596743488"
        }
        
        if secucode:
            params["filter"] = f"(SECUCODE=\"{secucode}\")"
        
        response = self._get_json(market_performance_url, params)
        
        if response and response.get("result") and response["result"].get("data"):
            return response["result"]["data"]
        elif response:
            return [{"error": response.get("message", "未知错误")}]
        else:
            return [{"error": "网络请求失败"}]
