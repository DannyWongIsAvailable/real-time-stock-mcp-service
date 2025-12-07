"""
网络爬虫数据源实现
src/stock_data_source.py
基于网络爬虫的数据源实现
"""

import logging
from typing import List, Optional, Dict, Any
from .data_source_interface import FinancialDataInterface, DataSourceError, NoDataFoundError, LoginError

logger = logging.getLogger(__name__)


class WebCrawlerDataSource(FinancialDataInterface):
    
    def __init__(self):
        self.kline_spider = None
        self.searcher = None
        self.real_time_spider = None
        self.fundamental_crawler = None
        self.valuation_crawler = None
        self.financial_analysis_crawler = None
    
    def initialize(self) -> bool:
        try:
            from src.crawler.basic_data import StockSearcher
            from src.crawler.technical_data import KlineSpider
            from src.crawler.real_time_data import RealTimeDataSpider
            from src.crawler.fundamental_data import FundamentalDataCrawler
            from src.crawler.valuation_data import ValuationDataCrawler
            from src.crawler.financial_analysis import FinancialAnalysisCrawler
            self.kline_spider = KlineSpider()
            self.searcher = StockSearcher()
            self.real_time_spider = RealTimeDataSpider()
            self.fundamental_crawler = FundamentalDataCrawler()
            self.valuation_crawler = ValuationDataCrawler()
            self.financial_analysis_crawler = FinancialAnalysisCrawler()
            return True
        except Exception as e:
            return False

    def cleanup(self):
        self.kline_spider = None
        self.searcher = None
        self.real_time_spider = None
        self.fundamental_crawler = None
        self.valuation_crawler = None
        self.financial_analysis_crawler = None

    def get_historical_k_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
    ) -> List[Dict]:
        beg = start_date.replace("-", "")
        end = end_date.replace("-", "")
        frequency_map = {
            "5": 5,
            "15": 15,
            "30": 30,
            "60": 60,
            "d": 101,
            "w": 102,
            "m": 103
        }
        klt = frequency_map.get(frequency, 101)
        return self.kline_spider.get_klines(
            stock_code=stock_code,
            beg=beg,
            end=end,
            klt=klt,
            fqt=1
        )

    def get_stock_search(
        self,
        keyword: str
    ) -> Optional[List[Dict]]:
        return self.searcher.search(keyword)

    def get_technical_indicators(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
    ) -> List[Dict]:
        return self.get_historical_k_data(stock_code, start_date, end_date, frequency)

    def get_last_trading_day(self) -> Optional[Dict]:
        return self.searcher.last_trading_day()

    def get_real_time_data(self, symbol: str) -> Dict:
        return self.real_time_spider.get_real_time_data(symbol)

    def get_main_business(self, stock_code: str, report_date: Optional[str] = None) -> Optional[List[Dict[Any, Any]]]:
        return self.fundamental_crawler.get_main_business(stock_code, report_date)

    def get_report_dates(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        return self.fundamental_crawler.get_report_dates(stock_code)

    def get_business_scope(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        return self.fundamental_crawler.get_business_scope(stock_code)

    def get_business_review(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        return self.fundamental_crawler.get_business_review(stock_code)

    def get_valuation_analysis(self, stock_code: str, indicator_type: int = 1, date_type: int = 3) -> Optional[Dict[Any, Any]]:
        return self.valuation_crawler.get_valuation_analysis(stock_code, indicator_type, date_type)

    def get_institutional_rating(self, stock_code: str, begin_time: str, end_time: str) -> Optional[List[Dict[Any, Any]]]:
        return self.valuation_crawler.get_institutional_rating(stock_code, begin_time, end_time)

    def get_main_financial_data(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        return self.fundamental_crawler.get_main_financial_data(stock_code)

    def get_financial_summary(self, stock_code: str, date_type_code: str = "004") -> Optional[List[Dict[Any, Any]]]:
        return self.financial_analysis_crawler.get_financial_summary(stock_code, date_type_code)

    def get_holder_number(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        return self.financial_analysis_crawler.get_holder_number(stock_code)

    def get_industry_valuation_comparison(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        return self.financial_analysis_crawler.get_industry_valuation_comparison(stock_code)
