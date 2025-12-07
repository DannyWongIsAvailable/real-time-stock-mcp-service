from src.crawler.base_crawler import EastMoneyBaseSpider

import requests
from typing import Optional, Dict, Any, List


class FinancialAnalysisCrawler(EastMoneyBaseSpider):
    """
    财报分析数据爬虫类

    用于获取股票的财报分析相关信息，如资产负债表、利润表、现金流量表等数据
    """
    
    OPERATING_REVENUE_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = 10,
    ):
        """
        初始化财报分析数据爬虫

        :param session: requests.Session 实例
        :param timeout: 请求超时时间
        """
        super().__init__(session, timeout)

    def get_financial_summary(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取业绩概况数据

        :param stock_code: 股票代码，包含交易所代码，格式如688041.SH
        :return: 业绩概况数据列表
        """
        params = {
            "reportName": "RPT_F10_FN_PERFORM",
            "columns": "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,ORG_CODE,REPORT_DATE,DATE_TYPE_CODE,DATE_TYPE,PARENTNETPROFIT,TOTALOPERATEREVE,KCFJCXSYJLR,PARENTNETPROFIT_RATIO,TOTALOPERATEREVE_RATIO,KCFJCXSYJLR_RATIO,YEAR,TYPE,IS_PUBLISH",
            "filter": f'(SECUCODE="{stock_code}")(DATE_TYPE_CODE in ("003","004"))(REPORT_DATE<=\'2025-09-30\')',
            "sortTypes": "-1",
            "sortColumns": "REPORT_DATE",
            "pageNumber": 1,
            "pageSize": 200,
            "source": "F10",
            "client": "PC",
            "v": "0748758885949164"
        }
        
        try:
            response = self._get_json(self.OPERATING_REVENUE_URL, params)
            # 检查响应是否成功
            if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                return response["result"]["data"]
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误")
                return [{"error": message}]
        except Exception as e:
            return [{"error": str(e)}]