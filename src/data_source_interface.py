"""
数据源接口定义

定义了获取股票数据的抽象接口，所有具体的数据源实现都应该实现这个接口。
这样设计可以方便地切换不同的数据源而不影响工具层的代码。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class DataSourceError(Exception):
    """Base exception for data source errors."""
    pass


class LoginError(DataSourceError):
    """Exception raised for login failures to the data source."""
    pass


class NoDataFoundError(DataSourceError):
    """Exception raised when no data is found for the given query."""
    pass


class FinancialDataInterface(ABC):
    """
    Abstract base class defining the interface for financial data sources.
    Implementations of this class provide access to specific financial data APIs
    """

    @abstractmethod
    def get_historical_k_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
    ) -> List[Dict]:
        """
        获取K线数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            K线数据列表，每个元素是一个字典，包含以下字段：
            date, open, close, high, low, volume, amount, amplitude, change_percent, change_amount, turnover_rate

        Raises:
            LoginError: If login to the data source fails.
            NoDataFoundError: If no data is found for the query.
            DataSourceError: For other data source related errors.
            ValueError: If input parameters are invalid.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_technical_indicators(
            self,
            stock_code: str,
            start_date: str,
            end_date: str,
            frequency: str = "d",
    ) -> List[Dict]:
        """
        获取技术指标数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            技术指标数据列表，每个元素是一个字典，包含以下字段：
            date, ma5, ma10, ma20, ma60, macd, macd_signal, macd_hist, rsi6, rsi12, rsi24, kdj_k, kdj_d, kdj_j

        Raises:
            LoginError: If login to the data source fails.
            NoDataFoundError: If no data is found for the query.
            DataSourceError: For other data source related errors.
            ValueError: If input parameters are invalid.
        """
        pass

    @abstractmethod
    def get_last_trading_day(self) -> Optional[Dict]:
        """
        获取最近交易日信息

        Returns:
            包含交易日信息的字典，例如：
            {
                "data": [
                    {"jybz": "1", "jyrq": "2025-12-04"},
                    {"jybz": "1", "jyrq": "2025-12-05"}
                ],
                "nowdate": "2025-12-04"
            }
            
            其中 jybz: 交易标志（1表示交易日，0表示休市）
                 jyrq: 交易日期
                 nowdate: 当前日期

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        pass

    @abstractmethod
    def get_real_time_data(self, symbol: str) -> Dict:
        """
        获取股票实时数据

        Args:
            symbol: 股票代码，包含交易所代码，格式例如 SZ300750

        Returns:
            实时股票数据字典，包含市场状态、报价等信息

        Raises:
            DataSourceError: 当数据源出现错误时
            NoDataFoundError: 当找不到指定股票数据时
        """
        pass

    @abstractmethod
    def get_main_business(self, stock_code: str, report_date: Optional[str] = None) -> Optional[List[Dict[Any, Any]]]:
        """
        获取主营构成分析

        Args:
            stock_code: 股票代码，包含交易所代码，如300059.SZ
            report_date: 报告日期，格式为YYYY-MM-DD，可选参数

        Returns:
            主营业务构成数据列表，每个元素是一个字典，包含主营业务信息
            如果没有找到数据或出错，返回包含错误信息的列表或者None

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        pass

    @abstractmethod
    def get_report_dates(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取报告日期

        Args:
            stock_code: 股票代码，包含交易所代码，格式如300059.SZ

        Returns:
            报告日期数据列表，每个元素是一个字典，包含报告日期信息
            如果没有找到数据或出错，返回包含错误信息的列表或者None

        Raises:
            DataSourceError: 当数据源出现错误时
        """
        pass
