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
    """
    基于网络爬虫的数据源实现
    """
    
    def __init__(self):
        """        
        初始化网络爬虫数据源
        """
        self.kline_spider = None
        self.searcher = None
        self.real_time_spider = None
        self.fundamental_crawler = None
        self.valuation_crawler = None
        self.financial_analysis_crawler = None
        logger.info("WebCrawler数据源实例已创建")
    
    def initialize(self) -> bool:
        """
        初始化数据源连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 初始化爬虫连接
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
            logger.info("WebCrawler连接成功")
            return True
        except Exception as e:
            logger.warning(f"WebCrawler初始化失败: {e}")
            return False

    def cleanup(self):
        """
        清理数据源连接，释放资源
        """
        # 清理爬虫连接（如果需要的话）
        self.kline_spider = None
        self.searcher = None
        self.real_time_spider = None
        self.fundamental_crawler = None
        self.valuation_crawler = None
        self.financial_analysis_crawler = None
        logger.info("WebCrawler连接已清理")

    # ==================== 行情数据 ====================
    
    def get_historical_k_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
    ) -> List[Dict]:
        """
        获取K线数据（原始数据，不做格式化处理）

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            K线数据列表，每个元素是一个字典，包含原始字段

        Raises:
            LoginError: If login to the data source fails.
            NoDataFoundError: If no data is found for the query.
            DataSourceError: For other data source related errors.
            ValueError: If input parameters are invalid.
        """
        # 检查kline_spider是否已初始化
        if self.kline_spider is None:
            logger.error("爬虫未初始化")
            raise DataSourceError("爬虫未初始化，请先调用initialize()方法")

        # 将日期格式从 YYYY-MM-DD 转换为 YYYYMMDD
        beg = start_date.replace("-", "")
        end = end_date.replace("-", "")

        # 将frequency映射到klt参数
        frequency_map = {
            "5": 5,      # 5分钟
            "15": 15,    # 15分钟
            "30": 30,    # 30分钟
            "60": 60,    # 60分钟
            "d": 101,    # 日线
            "w": 102,    # 周线
            "m": 103     # 月线
        }

        klt = frequency_map.get(frequency, 101)  # 默认日线

        try:
            # 调用爬虫获取数据
            klines = self.kline_spider.get_klines(
                stock_code=stock_code,
                beg=beg,
                end=end,
                klt=klt,
                fqt=1  # 前复权
            )

            # 如果没有数据，抛出NoDataFoundError异常
            if not klines:
                logger.warning(f"未找到股票 {stock_code} 在 {start_date} 到 {end_date} 期间的K线数据")
                raise NoDataFoundError(f"未找到股票 {stock_code} 在 {start_date} 到 {end_date} 期间的K线数据")

            # 直接返回原始数据字符串列表
            logger.info(f"成功获取股票 {stock_code} 的 {len(klines)} 条K线数据")
            return klines

        except NoDataFoundError:
            # 重新抛出NoDataFoundError
            raise
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise DataSourceError(f"获取K线数据失败: {e}")

    # ==================== 查询功能 ====================

    def get_stock_search(
        self,
        keyword: str
    ) -> Optional[List[Dict]]:
        """
        根据关键字搜索股票信息

        Args:
            keyword: 搜索关键字，可以是股票代码、股票名称等

        Returns:
            股票信息列表，每个元素是一个字典，包含股票的基本信息
            如：{'code': '300750', 'name': '宁德时代', 'pinyinString': 'ndsd', ...}
            如果没有找到匹配的股票，返回空列表

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查searcher是否已初始化
        if self.searcher is None:
            logger.error("股票搜索器未初始化")
            raise DataSourceError("股票搜索器未初始化，请先调用initialize()方法")

        try:
            # 调用搜索器获取数据
            search_results = self.searcher.search(keyword)

            # 如果没有数据，返回空列表
            if not search_results:
                logger.info(f"未找到与关键字 '{keyword}' 匹配的股票")
                return []

            logger.info(f"成功搜索到 {len(search_results)} 只与 '{keyword}' 相关的股票")
            return search_results

        except Exception as e:
            logger.error(f"搜索股票失败: {e}")
            raise DataSourceError(f"搜索股票失败: {e}")

    def get_technical_indicators(
            self,
            stock_code: str,
            start_date: str,
            end_date: str,
            frequency: str = "d",
    ) -> List[Dict]:
        """
        获取技术指标数据（原始数据，不做格式化处理）

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            包含K线数据和技术指标的原始数据

        Raises:
            LoginError: If login to the data source fails.
            NoDataFoundError: If no data is found for the query.
            DataSourceError: For other data source related errors.
            ValueError: If input parameters are invalid.
        """
        # 检查kline_spider是否已初始化
        if self.kline_spider is None:
            logger.error("爬虫未初始化")
            raise DataSourceError("爬虫未初始化，请先调用initialize()方法")

        # 首先获取K线数据
        k_data = self.get_historical_k_data(stock_code, start_date, end_date, frequency)

        if not k_data:
            raise NoDataFoundError(f"未找到股票 {stock_code} 的K线数据，无法计算技术指标")

        # 直接返回原始K线数据，不进行技术指标计算
        logger.info(f"成功获取股票 {stock_code} 的 {len(k_data)} 条K线数据")
        return k_data

    def get_last_trading_day(self) -> Optional[Dict]:
        """
        获取最近交易日信息

        Returns:
            包含交易日信息的字典

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查searcher是否已初始化
        if self.searcher is None:
            logger.error("股票搜索器未初始化")
            raise DataSourceError("股票搜索器未初始化，请先调用initialize()方法")

        try:
            # 调用搜索器获取最近交易日数据
            last_trading_day_data = self.searcher.last_trading_day()

            # 如果没有数据，返回None
            if not last_trading_day_data:
                logger.info("未获取到最近交易日信息")
                return None

            logger.info("成功获取最近交易日信息")
            return last_trading_day_data

        except Exception as e:
            logger.error(f"获取最近交易日信息失败: {e}")
            raise DataSourceError(f"获取最近交易日信息失败: {e}")

    def get_real_time_data(self, symbol: str) -> Dict:
        """
        获取股票实时数据

        Args:
            symbol: 股票代码，包含交易所代码，例如 SZ300750

        Returns:
            实时股票数据字典，包含市场状态、报价等信息

        Raises:
            DataSourceError: 当数据源出现错误时
            NoDataFoundError: 当找不到指定股票数据时
        """
        # 检查real_time_spider是否已初始化
        if self.real_time_spider is None:
            logger.error("实时数据爬虫未初始化")
            raise DataSourceError("实时数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取实时数据
            real_time_data = self.real_time_spider.get_real_time_data(symbol)

            # 如果没有数据，抛出NoDataFoundError异常
            if not real_time_data:
                logger.warning(f"未找到股票 {symbol} 的实时数据")
                raise NoDataFoundError(f"未找到股票 {symbol} 的实时数据")

            logger.info(f"成功获取股票 {symbol} 的实时数据")
            return real_time_data

        except NoDataFoundError:
            # 重新抛出NoDataFoundError
            raise
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            raise DataSourceError(f"获取实时数据失败: {e}")

    def get_main_business(self, stock_code: str, report_date: Optional[str] = None) -> Optional[List[Dict[Any, Any]]]:
        """
        获取主营构成分析

        Args:
            stock_code: 股票代码，包含交易所代码，如300059.SZ
            report_date: 报告日期，格式为YYYY-MM-DD，可选参数

        Returns:
            主营构成分析数据列表，每个元素是一个字典，包含主营业务信息
            如果没有找到数据或出错，返回包含错误信息的列表

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查fundamental_crawler是否已初始化
        if self.fundamental_crawler is None:
            logger.error("基本面数据爬虫未初始化")
            raise DataSourceError("基本面数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取主营构成分析数据
            main_business_data = self.fundamental_crawler.get_main_business(stock_code, report_date)

            # 如果没有数据，返回空列表
            if main_business_data is None:
                logger.info(f"未获取到股票 {stock_code} 的主营构成分析数据")
                return []

            logger.info(f"成功获取股票 {stock_code} 的主营构成分析数据")
            return main_business_data

        except Exception as e:
            logger.error(f"获取主营构成分析数据失败: {e}")
            raise DataSourceError(f"获取主营构成分析数据失败: {e}")

    def get_report_dates(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取报告日期

        Args:
            stock_code: 股票代码，包含交易所代码，如300059.SZ

        Returns:
            报告日期数据列表，每个元素是一个字典，包含报告日期信息
            如果没有找到数据或出错，返回包含错误信息的列表

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查fundamental_crawler是否已初始化
        if self.fundamental_crawler is None:
            logger.error("基本面数据爬虫未初始化")
            raise DataSourceError("基本面数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取报告日期数据
            report_dates_data = self.fundamental_crawler.get_report_dates(stock_code)

            # 如果没有数据，返回空列表
            if report_dates_data is None:
                logger.info(f"未获取到股票 {stock_code} 的报告日期数据")
                return []

            logger.info(f"成功获取股票 {stock_code} 的报告日期数据")
            return report_dates_data

        except Exception as e:
            logger.error(f"获取报告日期数据失败: {e}")
            raise DataSourceError(f"获取报告日期数据失败: {e}")

    def get_business_scope(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取主营业务范围

        Args:
            stock_code: 股票代码，包含交易所代码，如300059.SZ

        Returns:
            主营业务范围数据字典，包含主营业务范围信息
            如果没有找到数据或出错，返回包含错误信息的字典

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查fundamental_crawler是否已初始化
        if self.fundamental_crawler is None:
            logger.error("基本面数据爬虫未初始化")
            raise DataSourceError("基本面数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取主营业务范围数据
            business_scope_data = self.fundamental_crawler.get_business_scope(stock_code)

            # 如果没有数据，返回None
            if business_scope_data is None:
                logger.info(f"未获取到股票 {stock_code} 的主营业务范围数据")
                return None

            logger.info(f"成功获取股票 {stock_code} 的主营业务范围数据")
            return business_scope_data

        except Exception as e:
            logger.error(f"获取主营业务范围数据失败: {e}")
            raise DataSourceError(f"获取主营业务范围数据失败: {e}")

    def get_business_review(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取经营评述

        Args:
            stock_code: 股票代码，包含交易所代码，如300059.SZ

        Returns:
            经营评述数据字典，包含经营评述信息
            如果没有找到数据或出错，返回包含错误信息的字典

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查fundamental_crawler是否已初始化
        if self.fundamental_crawler is None:
            logger.error("基本面数据爬虫未初始化")
            raise DataSourceError("基本面数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取经营评述数据
            business_review_data = self.fundamental_crawler.get_business_review(stock_code)

            # 如果没有数据，返回None
            if business_review_data is None:
                logger.info(f"未获取到股票 {stock_code} 的经营评述数据")
                return None

            logger.info(f"成功获取股票 {stock_code} 的经营评述数据")
            return business_review_data

        except Exception as e:
            logger.error(f"获取经营评述数据失败: {e}")
            raise DataSourceError(f"获取经营评述数据失败: {e}")

    def get_valuation_analysis(self, stock_code: str, indicator_type: int = 1, date_type: int = 3) -> Optional[Dict[Any, Any]]:
        """
        获取估值分析数据

        Args:
            stock_code: 股票代码，包含交易所代码，格式如300059.SZ
            indicator_type: 指标类型
                          1 - 市盈率TTM
                          2 - 市净率MRQ
                          3 - 市销率TTM
                          4 - 市现率TTM
            date_type: 时间周期类型
                     1 - 1年
                     2 - 3年
                     3 - 5年
                     4 - 10年

        Returns:
            估值分析数据字典，包含以下字段：
            - SECUCODE: 股票代码
            - TRADE_DATE: 交易日期
            - INDICATOR_VALUE: 指标当前值
            - INDICATOR_TYPE: 指标类型中文名称
            - DATE_TYPE: 时间周期类型
            - STATISTICS_CYCLE: 统计周期中文名称
            - PERCENTILE_THIRTY: 30%历史分位数
            - PERCENTILE_FIFTY: 50%历史分位数(中位数)
            - PERCENTILE_SEVENTY: 70%历史分位数
            如果没有找到数据或出错，返回包含错误信息的字典

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查valuation_crawler是否已初始化
        if self.valuation_crawler is None:
            logger.error("估值数据爬虫未初始化")
            raise DataSourceError("估值数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取估值分析数据
            valuation_analysis_data = self.valuation_crawler.get_valuation_analysis(stock_code, indicator_type, date_type)

            # 如果没有数据，返回None
            if valuation_analysis_data is None or "error" in valuation_analysis_data:
                logger.info(f"未获取到股票 {stock_code} 的估值分析数据")
                return valuation_analysis_data  # 返回包含错误信息的字典

            logger.info(f"成功获取股票 {stock_code} 的估值分析数据")
            return valuation_analysis_data

        except Exception as e:
            logger.error(f"获取估值分析数据失败: {e}")
            raise DataSourceError(f"获取估值分析数据失败: {e}")

    def get_institutional_rating(self, stock_code: str, begin_time: str, end_time: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取机构评级数据

        Args:
            stock_code: 股票代码，不含交易所代码，格式如688041
            begin_time: 开始时间，格式如2025-10-23
            end_time: 结束时间，格式如2025-12-07

        Returns:
            机构评级数据列表，每个元素是一个字典，包含研报信息
            如果没有找到数据或出错，返回包含错误信息的列表

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查valuation_crawler是否已初始化
        if self.valuation_crawler is None:
            logger.error("估值数据爬虫未初始化")
            raise DataSourceError("估值数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取机构评级数据
            institutional_rating_data = self.valuation_crawler.get_institutional_rating(stock_code, begin_time, end_time)

            # 如果没有数据或返回错误，记录日志并返回结果
            if institutional_rating_data is None or (isinstance(institutional_rating_data, list) and len(institutional_rating_data) == 0):
                logger.info(f"未获取到股票 {stock_code} 在 {begin_time} 到 {end_time} 期间的机构评级数据")
                return []

            logger.info(f"成功获取股票 {stock_code} 在 {begin_time} 到 {end_time} 期间的机构评级数据")
            return institutional_rating_data

        except Exception as e:
            logger.error(f"获取机构评级数据失败: {e}")
            raise DataSourceError(f"获取机构评级数据失败: {e}")

    def get_main_financial_data(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取公司主要财务数据

        Args:
            stock_code: 股票代码，如601127

        Returns:
            公司主要财务数据字典，包含各种关键财务和业务指标
            如果没有找到数据或出错，返回包含错误信息的字典或者None

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查fundamental_crawler是否已初始化
        if self.fundamental_crawler is None:
            logger.error("基本面数据爬虫未初始化")
            raise DataSourceError("基本面数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取公司主要财务数据
            main_data = self.fundamental_crawler.get_main_financial_data(stock_code)

            # 如果没有数据或返回错误，记录日志并返回结果
            if main_data is None or "error" in main_data:
                logger.info(f"未获取到股票 {stock_code} 的公司主要财务数据")
                return main_data  # 返回包含错误信息的字典

            logger.info(f"成功获取股票 {stock_code} 的公司主要财务数据")
            return main_data

        except Exception as e:
            logger.error(f"获取公司主要财务数据失败: {e}")
            raise DataSourceError(f"获取公司主要财务数据失败: {e}")

    def get_financial_summary(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取业绩概况数据

        Args:
            stock_code: 股票代码，包含交易所代码，格式如688041.SH

        Returns:
            业绩概况数据列表，每个元素是一个字典，包含业绩概况信息
            如果没有找到数据或出错，返回包含错误信息的列表

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        # 检查financial_analysis_crawler是否已初始化
        if self.financial_analysis_crawler is None:
            logger.error("财务分析数据爬虫未初始化")
            raise DataSourceError("财务分析数据爬虫未初始化，请先调用initialize()方法")

        try:
            # 调用爬虫获取业绩概况数据
            financial_summary_data = self.financial_analysis_crawler.get_financial_summary(stock_code)

            # 如果没有数据，返回空列表
            if financial_summary_data is None:
                logger.info(f"未获取到股票 {stock_code} 的业绩概况数据")
                return []

            logger.info(f"成功获取股票 {stock_code} 的业绩概况数据")
            return financial_summary_data

        except Exception as e:
            logger.error(f"获取业绩概况数据失败: {e}")
            raise DataSourceError(f"获取业绩概况数据失败: {e}")