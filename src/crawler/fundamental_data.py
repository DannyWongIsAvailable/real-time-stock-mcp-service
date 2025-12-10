import json
import re

from src.crawler.base_crawler import EastMoneyBaseSpider

import requests
from typing import Optional, Dict, Any, List


class FundamentalDataCrawler(EastMoneyBaseSpider):
    """
    基本面数据爬虫类

    用于获取股票的基本面信息，如财务数据、公司概况等
    """
    
    MAIN_BUSINESS_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    REPORT_DATE_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    BUSINESS_SCOPE_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    BUSINESS_REVIEW_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    MAIN_DATA_URL = "https://push2.eastmoney.com/api/qt/stock/get"

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = 10,
    ):
        """
        初始化基本面数据爬虫
        
        :param session: requests.Session 实例
        :param timeout: 请求超时时间
        """
        super().__init__(session, timeout)

    @staticmethod
    def _parse_jsonp_custom(text: str) -> Optional[Dict]:
        """
        解析 JSONP 响应 (自定义版本，适配东方财富API)
        
        :param text: 形如 callback({...}) 的字符串
        :return: 解析后的字典，失败返回 None
        """
        # 使用更宽松的正则表达式匹配东方财富的JSONP格式
        match = re.search(r'^.+?\((.*)\);$', text.strip(), re.DOTALL)
        if not match:
            # 如果上面的模式不匹配，尝试原始模式
            match = re.search(r'^\w+\((.*)\)$', text.strip(), re.DOTALL)
            if not match:
                return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    def get_main_financial_data(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取公司主要财务数据
        
        :param stock_code: 股票代码
        :return: 公司主要财务数据字典
        """
        # 将股票代码转换为东方财富的 secid 格式
        secid = self.format_secid(stock_code)
        
        # 生成 callback 参数
        callback = self._generate_callback()
        
        params = {
            "invt": 2,
            "fltt": 1,
            "fields": "f57,f107,f162,f152,f167,f92,f59,f183,f184,f105,f185,f186,f187,f173,f188,f84,f116,f85,f117,f190,f189,f62,f55",
            "secid": secid,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "wbp2u": "|0|0|0|web",
            "dect": 1,
            "cb": callback
        }
        
        # 保存原始headers
        original_headers = self.headers.copy()
        
        # 添加特定于该API的请求头
        self.headers.update({
            "Referer": "https://www.eastmoney.com/",
            "Host": "push2.eastmoney.com"
        })
        
        try:
            response = self._get(self.MAIN_DATA_URL, params)
            # 检查响应是否成功
            if response.status_code == 200:
                parsed_response = self._parse_jsonp_custom(response.text)
                if parsed_response and parsed_response.get("rc") == 0:
                    # 只要rc为0就认为请求成功，即使data为空也应该返回
                    if "data" in parsed_response:
                        return parsed_response["data"]
                    else:
                        return {}
                else:
                    # 如果不成功，返回错误信息
                    message = parsed_response.get("message", "未知错误") if parsed_response else "未知错误"
                    return {"error": message}
            else:
                return {"error": f"HTTP错误: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            # 恢复原始headers
            self.headers = original_headers

    def get_report_dates(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取报告日期
        
        :param stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH
        :return: 报告日期列表
        """
        params = {
            "reportName": "RPT_F10_FN_MAINOP",
            "columns": "SECUCODE,REPORT_DATE",
            "distinct": "REPORT_DATE",
            "filter": f'(SECUCODE="{stock_code}")',
            "pageNumber": 1,
            "pageSize": "",
            "sortTypes": "-1",
            "sortColumns": "REPORT_DATE",
            "source": "HSF10",
            "client": "PC"
        }
        
        try:
            response = self._get_json(self.REPORT_DATE_URL, params)
            # 检查响应是否成功
            if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                return response["result"]["data"]
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误")
                return [{"error": message}]
        except Exception as e:
            return [{"error": str(e)}]

    def get_business_scope(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取主营业务范围
        
        :param stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH
        :return: 主营业务范围数据字典
        """
        params = {
            "reportName": "RPT_HSF9_BASIC_ORGINFO",
            "columns": "SECUCODE,SECURITY_CODE,BUSINESS_SCOPE",
            "filter": f'(SECUCODE="{stock_code}")',
            "pageNumber": 1,
            "pageSize": 1,
            "source": "HSF10",
            "client": "PC"
        }
        
        try:
            response = self._get_json(self.BUSINESS_SCOPE_URL, params)
            # 检查响应是否成功
            if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                return response["result"]["data"][0] if response["result"]["data"] else None
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误")
                return {"error": message}
        except Exception as e:
            return {"error": str(e)}

    def get_business_review(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取经营评述
        
        :param stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH
        :return: 经营评述数据字典
        """
        params = {
            "reportName": "RPT_F10_OP_BUSINESSANALYSIS",
            "columns": "SECUCODE,SECURITY_CODE,REPORT_DATE,BUSINESS_REVIEW",
            "filter": f'(SECUCODE="{stock_code}")',
            "pageNumber": 1,
            "pageSize": 1,
            "source": "HSF10",
            "client": "PC"
        }
        
        try:
            response = self._get_json(self.BUSINESS_REVIEW_URL, params)
            # 检查响应是否成功
            if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                return response["result"]["data"][0] if response["result"]["data"] else None
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误")
                return {"error": message}
        except Exception as e:
            return {"error": str(e)}


    def get_main_business(self, stock_code: str, report_date: Optional[str] = None) -> Optional[List[Dict[Any, Any]]]:
        """
        获取主营业务构成
        
        :param stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH
        :param report_date: 报告日期，格式为YYYY-MM-DD，可选参数
        :return: 主营业务构成数据字典
        """
        # 构建基础filter参数
        filter_param = f'(SECUCODE="{stock_code}")'
        
        # 如果提供了报告日期，则添加到filter中
        if report_date:
            filter_param += f'(REPORT_DATE=\'{report_date}\')'
        
        params = {
            "reportName": "RPT_F10_FN_MAINOP",
            "columns": "SECUCODE,SECURITY_CODE,REPORT_DATE,MAINOP_TYPE,ITEM_NAME,MAIN_BUSINESS_INCOME,MBI_RATIO,MAIN_BUSINESS_COST,MBC_RATIO,MAIN_BUSINESS_RPOFIT,MBR_RATIO,GROSS_RPOFIT_RATIO,RANK",
            "filter": filter_param,
            "pageNumber": 1,
            "pageSize": 200,
            "sortTypes": "1,1",
            "sortColumns": "MAINOP_TYPE,RANK",
            "source": "HSF10",
            "client": "PC"
        }
        
        try:
            response = self._get_json(self.MAIN_BUSINESS_URL, params)
            # 检查响应是否成功
            if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                return response["result"]["data"]
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误")
                return [{"error": message}]
        except Exception as e:
            return [{"error": str(e)}]