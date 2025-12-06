import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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

    def get_report_dates(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取报告日期
        
        :param stock_code: 股票代码，包含交易所代码，格式如688041.SH
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

    def get_financial_summary(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取财务摘要数据
        
        :param stock_code: 股票代码
        :return: 财务摘要数据字典
        """
        # TODO: 实现获取财务摘要数据的方法
        pass

    def get_company_profile(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取公司概况
        
        :param stock_code: 股票代码
        :return: 公司概况数据字典
        """
        # TODO: 实现获取公司概况的方法
        pass

    def get_main_business(self, stock_code: str, report_date: Optional[str] = None) -> Optional[List[Dict[Any, Any]]]:
        """
        获取主营业务构成
        
        :param stock_code: 股票代码，包含交易所代码，格式如300059.SZ
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

    def get_shareholder_info(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取股东信息
        
        :param stock_code: 股票代码
        :return: 股东信息数据字典
        """
        # TODO: 实现获取股东信息的方法
        pass

    def get_dividend_info(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取分红信息
        
        :param stock_code: 股票代码
        :return: 分红信息数据字典
        """
        # TODO: 实现获取分红信息的方法
        pass


if __name__ == '__main__':
    # TODO: 添加测试代码
    pass