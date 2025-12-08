from src.crawler.base_crawler import EastMoneyBaseSpider

import requests
from typing import Optional, Dict, Any, List


class FinancialAnalysisCrawler(EastMoneyBaseSpider):
    """
    财报分析数据爬虫类

    用于获取股票的财报分析相关信息，如资产负债表、利润表、现金流量表等数据
    """
    
    BASE_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"

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

    def get_financial_summary(self, stock_code: str, date_type_code: str = "004") -> Optional[List[Dict[Any, Any]]]:
        """
        获取业绩概况数据

        :param stock_code: 股票代码，包含交易所代码，格式如688041.SH
        :param date_type_code: 报告类型代码
                             "001" - 一季度报告
                             "002" - 半年度报告
                             "003" - 三季度报告
                             "004" - 年度报告
        :return: 业绩概况数据列表
        """
        params = {
            "reportName": "RPT_F10_FN_PERFORM",
            "columns": "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,ORG_CODE,REPORT_DATE,DATE_TYPE_CODE,DATE_TYPE,PARENTNETPROFIT,TOTALOPERATEREVE,KCFJCXSYJLR,PARENTNETPROFIT_RATIO,TOTALOPERATEREVE_RATIO,KCFJCXSYJLR_RATIO,YEAR,TYPE,IS_PUBLISH",
            "filter": f'(SECUCODE="{stock_code}")(DATE_TYPE_CODE in ("{date_type_code}"))',
            "sortTypes": "-1",
            "sortColumns": "REPORT_DATE",
            "pageNumber": 1,
            "pageSize": 200,
            "source": "F10",
            "client": "PC",
            "v": "0748758885949164"
        }
        
        try:
            response = self._get_json(self.BASE_URL, params)
            # 检查响应是否成功
            if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                return response["result"]["data"]
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误")
                return [{"error": message}]
        except Exception as e:
            return [{"error": str(e)}]

    def get_holder_number(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取股东户数数据

        :param stock_code: 股票代码，包含交易所代码，格式如688041.SH
        :return: 股东户数数据列表
        """
        params = {
            "reportName": "RPT_HOLDERNUM_DET",
            "columns": "SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,HOLDER_NUM,REPORT,END_DATE,CLOSE_PRICE",
            "filter": f'(SECUCODE="{stock_code}")',
            "sortTypes": "-1",
            "sortColumns": "END_DATE",
            "pageNumber": 1,
            "pageSize": 200,
            "source": "F10",
            "client": "PC",
            "v": "07356204940503169"
        }
        
        try:
            response = self._get_json(self.BASE_URL, params)
            # 检查响应是否成功
            if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                return response["result"]["data"]
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误")
                return [{"error": message}]
        except Exception as e:
            return [{"error": str(e)}]

    def get_latest_report_dates(self, stock_code: str) -> Optional[List[str]]:
        """
        获取最新三个报告日期

        :param stock_code: 股票代码，包含交易所代码，如688041.SH
        :return: 最新三个报告日期列表，格式为 YYYY-MM-DD
        """
        params = {
            "reportName": "RPT_F10_INDUSTRY_COMPARED",
            "columns": "REPORT_DATE",
            "quoteColumns": "",
            "filter": f'(SECUCODE="{stock_code}")',
            "sortTypes": "1,-1",
            "sortColumns": "IS_SELF,TOTALOPERATEREVE_RANK",
            "pageNumber": 1,
            "pageSize": 4,
            "source": "F10",
            "client": "PC",
            "v": "005130138354940328"
        }
        
        try:
            response = self._get_json(self.BASE_URL, params)
            # 检查响应是否成功
            if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                data = response["result"]["data"]
                if data:
                    dates = []
                    seen_dates = set()
                    for item in data:
                        report_date = item.get("REPORT_DATE")
                        if report_date:
                            # 格式化为 YYYY-MM-DD
                            formatted_date = report_date.split()[0]
                            if formatted_date not in seen_dates:
                                dates.append(formatted_date)
                                seen_dates.add(formatted_date)
                    return dates
                else:
                    return []
            else:
                # 如果不成功，记录错误信息
                message = response.get("message", "未知错误")
                return [message]
        except Exception as e:
            return [f"获取最新报告日期时发生异常: {str(e)}"]

    def get_industry_profit_comparison(self, stock_code: str, report_dates: List[str] = None) -> Optional[List[Dict[Any, Any]]]:
        """
        获取同行业公司盈利数据

        :param stock_code: 股票代码，数字后必须添加交易所代码，如688041.SH
        :param report_dates: 报告日期列表，格式为 YYYY-MM-DD，如果未提供则使用最新三个报告日期
        :return: 同行业公司盈利数据列表
        """
        # 如果没有提供报告日期，则获取最新的三个报告日期
        if not report_dates:
            report_dates = self.get_latest_report_dates(stock_code)
            if not report_dates or isinstance(report_dates[0], str) and "异常" in report_dates[0]:
                # 尝试使用一个默认的近期报告日期
                import datetime
                # 使用今年的年报日期作为备选方案
                curr_year = datetime.datetime.now().year
                default_date = f"{curr_year}-9-30"
                print(f"无法获取最新报告日期，尝试使用默认日期: {default_date}")
                report_dates = [default_date]

        all_data = []
        for report_date in report_dates:
            params = {
                "reportName": "RPT_F10_INDUSTRY_COMPARED",
                "columns": "ALL",
                "quoteColumns": "",
                "filter": f'(SECUCODE="{stock_code}")(REPORT_DATE=\'{report_date}\')',
                "sortTypes": "-1,1",
                "sortColumns": "IS_SELF,TOTALOPERATEREVE_RANK",
                "pageNumber": 1,
                "pageSize": 4,
                "source": "F10",
                "client": "PC",
                "v": "08494015389572059"
            }
            
            try:
                response = self._get_json(self.BASE_URL, params)
                # 检查响应是否成功
                if response.get("code") == 0 and response.get("success") is True and response.get("result"):
                    all_data.extend(response["result"]["data"])
                else:
                    # 如果不成功，添加错误信息
                    message = response.get("message", "未知错误")
                    all_data.extend([{"error": message}])
            except Exception as e:
                all_data.extend([{"error": str(e)}])
        
        return all_data
