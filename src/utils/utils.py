"""
通用工具函数
"""

import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional


def setup_logging(level=logging.INFO):
    """
    配置日志系统
    
    Args:
        level: 日志级别
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )


def format_date(date_obj: datetime) -> str:
    """
    将datetime对象格式化为YYYY-MM-DD字符串
    
    Args:
        date_obj: datetime对象
        
    Returns:
        格式化的日期字符串
    """
    return date_obj.strftime('%Y-%m-%d')


def parse_date(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串为datetime对象
    
    Args:
        date_str: 日期字符串 (YYYY-MM-DD)
        
    Returns:
        datetime对象，解析失败返回None
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


def get_date_range(days: int = 30) -> tuple[str, str]:
    """
    获取从今天往前指定天数的日期范围
    
    Args:
        days: 天数
        
    Returns:
        (start_date, end_date) 元组
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return format_date(start_date), format_date(end_date)


def format_number(num: float, decimal_places: int = 2) -> str:
    """
    格式化数字，添加千位分隔符
    
    Args:
        num: 数字
        decimal_places: 小数位数
        
    Returns:
        格式化后的字符串
    """
    if num is None:
        return 'N/A'
    return f'{num:,.{decimal_places}f}'

def format_large_number(value: float) -> str:
    """
    格式化数值为亿或万单位

    Args:
        value: 数值

    Returns:
        格式化后的字符串
    """
    abs_value = abs(value)
    if abs_value >= 100000000:  # 大于等于1亿
        return f"{'+' if value >= 0 else ''}{value / 100000000:.2f}亿"
    elif abs_value >= 10000:  # 大于等于1万
        return f"{'+' if value >= 0 else ''}{value / 10000:.2f}万"
    else:
        return f"{'+' if value >= 0 else ''}{value:.0f}"


def format_percentage(num: float, decimal_places: int = 2) -> str:
    """
    格式化百分比
    
    Args:
        num: 数字（如 0.05 表示 5%）
        decimal_places: 小数位数
        
    Returns:
        格式化后的百分比字符串
    """
    if num is None:
        return 'N/A'
    return f'{num * 100:.{decimal_places}f}%'


def safe_float(value, default=0.0) -> float:
    """
    安全地将值转换为浮点数
    
    Args:
        value: 待转换的值
        default: 默认值
        
    Returns:
        浮点数
    """
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0) -> int:
    """
    安全地将值转换为整数
    
    Args:
        value: 待转换的值
        default: 默认值
        
    Returns:
        整数
    """
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_timestamp(timestamp) -> str:
    """
    将时间戳转换为可读的时间字符串
    
    Args:
        timestamp: 时间戳（毫秒或秒）
        
    Returns:
        格式化后的时间字符串
    """
    if not timestamp:
        return "N/A"
    
    try:
        # 如果时间戳是字符串，先转换为数字
        if isinstance(timestamp, str):
            timestamp = int(timestamp)
        
        # 雪球API返回的时间戳通常是毫秒单位
        if timestamp > 1000000000000:  # 判断是否为毫秒时间戳
            timestamp = timestamp / 1000
            
        # 转换为本地时间字符串
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, Exception):
        return str(timestamp)


def add_exchange_prefix(stock_code: str) -> str:
    """
    为股票代码自动添加交易所代码前缀
    
    Args:
        stock_code: 股票代码，如 300750
        
    Returns:
        添加前缀后的股票代码，如 SZ.300750
    """
    if not stock_code:
        return stock_code
    
    # 根据股票代码自动识别交易所
    exchange = _get_exchange_code(stock_code)
    return f"{exchange}.{stock_code}"


def add_exchange_suffix(stock_code: str) -> str:
    """
    为股票代码自动添加交易所代码后缀
    
    Args:
        stock_code: 股票代码，如 300750
        
    Returns:
        添加后缀后的股票代码，如 300750.SZ
    """
    if not stock_code:
        return stock_code
    
    # 根据股票代码自动识别交易所
    exchange = _get_exchange_code(stock_code)
    return f"{stock_code}.{exchange}"


def _get_exchange_code(stock_code: str) -> str:
    """
    根据股票代码自动识别交易所代码

    港股判断必须放在 A 股的前面，
    因为港股也常以 0 开头（如 00700、01810），否则会被误判为 SZ。
    """
    if not stock_code:
        return "SH"  # 默认上海交易所

    code = stock_code.upper()

    # ---- 1. 先判断港股 ----
    # 规则：5 位数字 或 结尾 .HK
    if code.endswith(".HK"):
        return "HK"
    if code.isdigit() and len(code) == 5:
        return "HK"

    # ---- 2. 再判断 A 股 ----
    # 上海：6xxxx、5xxxx
    if code.startswith(("6", "5")):
        return "SH"

    # 深圳：0xxxx、3xxxx
    if code.startswith(("0", "3")):
        return "SZ"

    # ---- 3. 再判断北交所 ----
    if code.startswith(("4", "8")):
        return "BJ"

    # ---- 4. 兜底 ----
    return "SH"
