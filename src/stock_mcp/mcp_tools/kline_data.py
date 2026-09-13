"""
K线数据工具
src/mcp_tools/kline_data.py
提供K线数据查询和分析功能
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from fastmcp import FastMCP
from stock_mcp.data_source_interface import FinancialDataInterface
from stock_mcp.utils.markdown_formatter import (
    format_list_to_markdown_table,
    format_markdown_report,
    pick_columns,
)
from stock_mcp.utils.utils import format_number, format_large_number

logger = logging.getLogger(__name__)

_CN_TZ = timezone(timedelta(hours=8))

# 雪球 K 线 column 字段（与 API 返回顺序一致）
XUEQIU_KLINE_COLUMNS = [
    "timestamp",
    "volume",
    "open",
    "high",
    "low",
    "close",
    "chg",
    "percent",
    "turnoverrate",
    "amount",
    "volume_post",
    "amount_post",
    "pe",
    "pb",
    "ps",
    "pcf",
    "market_capital",
    "balance",
    "hold_volume_cn",
    "hold_ratio_cn",
    "net_volume_cn",
    "hold_volume_hk",
    "hold_ratio_hk",
    "net_volume_hk",
]

XUEQIU_KLINE_LABELS = {
    "timestamp": "日期",
    "volume": "成交量",
    "open": "开盘",
    "high": "最高",
    "low": "最低",
    "close": "收盘",
    "chg": "涨跌额",
    "percent": "涨跌幅",
    "turnoverrate": "换手率",
    "amount": "成交额",
    "volume_post": "盘后成交量",
    "amount_post": "盘后成交额",
    "pe": "市盈率(PE)",
    "pb": "市净率(PB)",
    "ps": "市销率(PS)",
    "pcf": "市现率(PCF)",
    "market_capital": "总市值",
    "balance": "余额",
    "hold_volume_cn": "陆股通持股量",
    "hold_ratio_cn": "陆股通持股比例",
    "net_volume_cn": "陆股通净买入",
    "hold_volume_hk": "港股通持股量",
    "hold_ratio_hk": "港股通持股比例",
    "net_volume_hk": "港股通净买入",
}


def _format_nullable(value: Any, formatter) -> str:
    if value is None:
        return "-"
    return formatter(value)


def format_kline_row(kline: Dict[str, Any]) -> Dict[str, str]:
    """将单条雪球 K 线字典格式化为 Markdown 表格行（中文列名）"""
    open_price = float(kline.get("open") or 0)
    close_price = float(kline.get("close") or 0)
    high_price = float(kline.get("high") or 0)
    low_price = float(kline.get("low") or 0)

    if close_price > open_price:
        status = "上涨（阳线）"
    elif close_price < open_price:
        status = "下跌（阴线）"
    else:
        status = "平盘（十字星）"

    amplitude = (high_price - low_price) / open_price * 100 if open_price else 0.0
    ts = kline.get("timestamp")
    date_str = (
        datetime.fromtimestamp(ts / 1000, tz=_CN_TZ).strftime("%Y-%m-%d")
        if ts else "-"
    )

    percent = float(kline.get("percent") or 0)
    row = {
        "日期": date_str,
        "K线状态": status,
        "开盘": format_number(open_price),
        "最高": format_number(high_price),
        "最低": format_number(low_price),
        "收盘": format_number(close_price),
        "涨跌额": _format_nullable(kline.get("chg"), lambda v: format_number(float(v))),
        "涨跌幅": f"{'+' if percent > 0 else ''}{percent:.2f}%",
        "换手率": _format_nullable(
            kline.get("turnoverrate"), lambda v: f"{float(v):.2f}%"
        ),
        "成交量": _format_nullable(kline.get("volume"), lambda v: format_large_number(int(v))),
        "成交额": _format_nullable(kline.get("amount"), lambda v: format_large_number(float(v))),
        "振幅": f"{amplitude:.2f}%",
        "盘后成交量": _format_nullable(
            kline.get("volume_post"), lambda v: format_large_number(int(v))
        ),
        "盘后成交额": _format_nullable(
            kline.get("amount_post"), lambda v: format_large_number(float(v))
        ),
        "市盈率(PE)": _format_nullable(kline.get("pe"), lambda v: f"{float(v):.4f}"),
        "市净率(PB)": _format_nullable(kline.get("pb"), lambda v: f"{float(v):.4f}"),
        "市销率(PS)": _format_nullable(kline.get("ps"), lambda v: f"{float(v):.4f}"),
        "市现率(PCF)": _format_nullable(kline.get("pcf"), lambda v: f"{float(v):.4f}"),
        "总市值": _format_nullable(
            kline.get("market_capital"), lambda v: format_large_number(float(v))
        ),
        "余额": _format_nullable(kline.get("balance"), lambda v: format_large_number(float(v))),
        "陆股通持股量": _format_nullable(
            kline.get("hold_volume_cn"), lambda v: format_large_number(int(v))
        ),
        "陆股通持股比例": _format_nullable(
            kline.get("hold_ratio_cn"), lambda v: f"{float(v):.2f}%"
        ),
        "陆股通净买入": _format_nullable(
            kline.get("net_volume_cn"), lambda v: format_large_number(int(v))
        ),
        "港股通持股量": _format_nullable(
            kline.get("hold_volume_hk"), lambda v: format_large_number(int(v))
        ),
        "港股通持股比例": _format_nullable(
            kline.get("hold_ratio_hk"), lambda v: f"{float(v):.2f}%"
        ),
        "港股通净买入": _format_nullable(
            kline.get("net_volume_hk"), lambda v: format_large_number(int(v))
        ),
    }
    return row


KLINE_PRICE_COLUMNS = [
    "日期",
    "K线状态",
    "开盘",
    "最高",
    "最低",
    "收盘",
    "涨跌额",
    "涨跌幅",
    "换手率",
    "成交量",
    "成交额",
    "振幅",
]

KLINE_VALUATION_COLUMNS = [
    "日期",
    "市盈率(PE)",
    "市净率(PB)",
    "市销率(PS)",
    "市现率(PCF)",
    "总市值",
    "盘后成交量",
    "盘后成交额",
    "余额",
    "陆股通持股量",
    "陆股通持股比例",
    "陆股通净买入",
    "港股通持股量",
    "港股通持股比例",
    "港股通净买入",
]

TECH_PRICE_COLUMNS = [
    "交易日期",
    "收盘价",
    "开盘价",
    "最高价",
    "最低价",
    "移动平均线价格（MA5 MA10 MA20，单位：元）",
    "5日平均成交金额",
    "支撑位",
    "压力位",
]

TECH_MACD_COLUMNS = ["交易日期", "DIF", "DEA", "MACD", "MACD信号"]
TECH_KDJ_COLUMNS = ["交易日期", "K", "D", "J", "KDJ信号"]
TECH_RSI_COLUMNS = ["交易日期", "RSI1(6日)", "RSI2(12日)", "RSI3(24日)", "RSI信号"]
TECH_BOLL_COLUMNS = ["交易日期", "BOLL上轨", "BOLL中轨", "BOLL下轨", "BOLL信号"]
TECH_BIAS_WR_COLUMNS = [
    "交易日期",
    "BIAS1(6日)",
    "BIAS2(12日)",
    "BIAS3(24日)",
    "BIAS信号",
    "WR1(10日)",
    "WR2(20日)",
    "WR信号",
]
TECH_MARKET_COLUMNS = [
    "交易日期",
    "近60日区间涨跌幅",
    "近60日区间振幅",
    "近60日沪深300涨跌幅",
    "近60日区间换手率",
]


EASTMONEY_KLINE_COLUMNS = [
    "日期",
    "K线状态",
    "开盘",
    "最高",
    "最低",
    "收盘",
    "涨跌额",
    "涨跌幅",
    "振幅",
    "换手率",
    "成交量",
    "成交额",
]


def format_kline_markdown(
    stock_code: str,
    formatted_data: List[Dict[str, str]],
    frequency: str,
) -> str:
    """将 K 线拆分为多张窄表，便于 Agent 端 Markdown 渲染。"""
    sections = [
        (
            "价格与成交",
            format_list_to_markdown_table(
                pick_columns(formatted_data, KLINE_PRICE_COLUMNS)
            ),
        ),
        (
            "估值与资金",
            format_list_to_markdown_table(
                pick_columns(formatted_data, KLINE_VALUATION_COLUMNS)
            ),
        ),
    ]
    return format_markdown_report(
        f"{stock_code} K线数据",
        sections=sections,
        footnote=f"💡 显示 {len(formatted_data)} 条K线数据，频率: {frequency}",
    )


def parse_eastmoney_klines(klines: List[str]) -> List[Dict[str, Any]]:
    """解析东方财富 K 线原始字符串列表为结构化字典。"""
    result = []
    for kline in klines:
        fields = kline.split(",")
        if len(fields) >= 11:
            result.append({
                "date": fields[0],
                "open": float(fields[1]),
                "close": float(fields[2]),
                "high": float(fields[3]),
                "low": float(fields[4]),
                "volume": int(fields[5]),
                "amount": float(fields[6]),
                "amplitude": float(fields[7]),
                "change_percent": float(fields[8]),
                "change_amount": float(fields[9]),
                "turnover_rate": float(fields[10]),
            })
    return result


def format_eastmoney_kline_row(kline: Dict[str, Any]) -> Dict[str, str]:
    """将解析后的东方财富 K 线字典格式化为 Markdown 表格行（中文列名）"""
    open_price = kline["open"]
    close_price = kline["close"]
    high_price = kline["high"]
    low_price = kline["low"]

    if close_price > open_price:
        status = "上涨（阳线）"
    elif close_price < open_price:
        status = "下跌（阴线）"
    else:
        status = "平盘（十字星）"

    percent = kline["change_percent"]
    return {
        "日期": kline["date"],
        "K线状态": status,
        "开盘": format_number(open_price),
        "最高": format_number(high_price),
        "最低": format_number(low_price),
        "收盘": format_number(close_price),
        "涨跌额": format_number(kline["change_amount"]),
        "涨跌幅": f"{'+' if percent > 0 else ''}{percent:.2f}%",
        "振幅": f"{kline['amplitude']:.2f}%",
        "换手率": f"{kline['turnover_rate']:.2f}%",
        "成交量": format_large_number(kline["volume"]),
        "成交额": format_large_number(kline["amount"]),
    }


def format_eastmoney_kline_markdown(
    stock_code: str,
    formatted_data: List[Dict[str, str]],
    frequency: str,
) -> str:
    """将东方财富 K 线格式化为 Markdown 表格。"""
    return format_markdown_report(
        f"{stock_code} K线数据",
        table_data=pick_columns(formatted_data, EASTMONEY_KLINE_COLUMNS),
        footnote=f"💡 显示 {len(formatted_data)} 条K线数据，频率: {frequency}",
    )


def format_technical_indicators_markdown(
    stock_code: str,
    stock_name: str,
    formatted_data: List[Dict[str, str]],
) -> str:
    """将技术指标拆分为多张子表，长文本单独作为脚注。"""
    sections = [
        (
            "价格与均线",
            format_list_to_markdown_table(
                pick_columns(formatted_data, TECH_PRICE_COLUMNS)
            ),
        ),
        (
            "MACD",
            format_list_to_markdown_table(pick_columns(formatted_data, TECH_MACD_COLUMNS)),
        ),
        (
            "KDJ",
            format_list_to_markdown_table(pick_columns(formatted_data, TECH_KDJ_COLUMNS)),
        ),
        (
            "RSI",
            format_list_to_markdown_table(pick_columns(formatted_data, TECH_RSI_COLUMNS)),
        ),
        (
            "BOLL",
            format_list_to_markdown_table(pick_columns(formatted_data, TECH_BOLL_COLUMNS)),
        ),
        (
            "BIAS / WR",
            format_list_to_markdown_table(
                pick_columns(formatted_data, TECH_BIAS_WR_COLUMNS)
            ),
        ),
        (
            "市场对比",
            format_list_to_markdown_table(
                pick_columns(formatted_data, TECH_MARKET_COLUMNS)
            ),
        ),
    ]

    footnote_parts = [f"💡 显示 {len(formatted_data)} 条技术指标数据"]
    if formatted_data:
        latest = formatted_data[-1]
        explain = latest.get("趋势量能分析", "").strip()
        if explain:
            footnote_parts.append(f"\n\n分析解读：{explain}")

    return format_markdown_report(
        f"{stock_name}({stock_code}) 技术指标数据",
        sections=sections,
        footnote="\n".join(footnote_parts),
    )


def format_kline_data(klines: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    格式化雪球 K 线数据列表，用于 Markdown 表格展示

    Args:
        klines: 雪球 API 返回的 K 线字典列表（column 字段名 -> 值）

    Returns:
        中文列名的展示字典列表
    """
    return [format_kline_row(kline) for kline in klines]


def format_eastmoney_kline_data(klines: List[str]) -> List[Dict[str, str]]:
    """
    解析并格式化东方财富 K 线数据列表，用于 Markdown 表格展示

    Args:
        klines: 东方财富 API 返回的 K 线字符串列表

    Returns:
        中文列名的展示字典列表
    """
    parsed = parse_eastmoney_klines(klines)
    return [format_eastmoney_kline_row(kline) for kline in parsed]


def format_technical_indicators_data(technical_data: List[Dict]) -> List[Dict]:
    """
    格式化技术指标数据

    Args:
        technical_data: 原始技术指标数据列表

    Returns:
        格式化后的技术指标数据列表
    """
    formatted_data = []
    
    for item in technical_data:
        # 解析交易日期，只保留日期部分
        trade_date = item.get('TRADEDATE', '').split(' ')[0]
        
        # 格式化各项技术指标
        formatted_item = {
            '交易日期': trade_date,
            '收盘价': format_number(item.get('NEW', 0)),
            '开盘价': format_number(item.get('OPEN', 0)),
            '最高价': format_number(item.get('HIGH', 0)),
            '最低价': format_number(item.get('LOW', 0)),
            '移动平均线价格（MA5 MA10 MA20，单位：元）': item.get('AVG_PRICE', ''),
            '5日平均成交金额': f"{format_large_number(item.get('AVG_AMOUNT_5DAYS', 0))} 元" if item.get(
                'AVG_AMOUNT_5DAYS') else '',

            # MACD指标
            'DIF': f"{item.get('DIF', 0):.4f}",
            'DEA': f"{item.get('DEA', 0):.4f}",
            'MACD': f"{item.get('MACD', 0):.4f}",
            'MACD信号': item.get('MACDCOUT', ''),
            
            # KDJ指标
            'K': f"{item.get('K', 0):.2f}",
            'D': f"{item.get('D', 0):.2f}",
            'J': f"{item.get('J', 0):.2f}",
            'KDJ信号': item.get('KDJOUT', ''),
            
            # RSI指标
            'RSI1(6日)': f"{item.get('RSI1', 0):.2f}",
            'RSI2(12日)': f"{item.get('RSI2', 0):.2f}",
            'RSI3(24日)': f"{item.get('RSI3', 0):.2f}",
            'RSI信号': item.get('RSIOUT', ''),
            
            # BOLL指标
            'BOLL上轨': format_number(item.get('UPPER', 0)),
            'BOLL中轨': format_number(item.get('MID', 0)),
            'BOLL下轨': format_number(item.get('LOWER', 0)),
            'BOLL信号': item.get('BOLLOUT', ''),
            
            # BIAS指标
            'BIAS1(6日)': f"{item.get('BIAS1', 0):.2f}",
            'BIAS2(12日)': f"{item.get('BIAS2', 0):.2f}",
            'BIAS3(24日)': f"{item.get('BIAS3', 0):.2f}",
            'BIAS信号': item.get('BIASOUT', ''),
            
            # WR指标
            'WR1(10日)': f"{item.get('WR1', 0):.2f}",
            'WR2(20日)': f"{item.get('WR2', 0):.2f}",
            'WR信号': item.get('WROUT', ''),
            
            # 市场数据
            '近60日区间涨跌幅': f"{item.get('PCTCHANGE_STOCK', 0):+.2f}%",
            '近60日区间振幅': f"{item.get('SWING', 0):.2f}%",
            '近60日沪深300涨跌幅': f"{item.get('PCTCHANGE_INDEX', 0):+.2f}%",
            '近60日区间换手率': f"{item.get('AVGTURN', 0):.2f}%",

            '支撑位': f"{format_number(item.get('SUPPORT_LEVEL', 0))} 元" if item.get('SUPPORT_LEVEL') else '',
            '压力位': f"{format_number(item.get('PRESSURE_LEVEL', 0))} 元" if item.get('PRESSURE_LEVEL') else '',
            '趋势量能分析': item.get('WORDS_EXPLAIN', '')
        }
        
        formatted_data.append(formatted_item)
    
    return formatted_data


def format_intraday_changes_data(intraday_changes: List[str]) -> List[Dict]:
    """
    格式化分时图盘口异动数据

    Args:
        intraday_changes: 原始分时图盘口异动数据列表

    Returns:
        格式化后的分时图盘口异动数据列表
    """
    formatted_data = []
    
    # 事件类型码含义映射
    event_type_map = {
        1: "有大买盘",
        101: "有大卖盘",
        2: "大笔买入",
        102: "大笔卖出",
        201: "封涨停板",
        301: "封跌停板",
        202: "打开涨停",
        302: "打开跌停",
        203: "高开5日线",
        303: "低开5日线",
        204: "60日新高",
        304: "60日新低",
        401: "向上缺口",
        501: "向下缺口",
        402: "火箭发射",
        502: "高台跳水",
        403: "快速反弹",
        503: "快速下跌",
        404: "竞价上涨",
        504: "竞价下跌",
        405: "60日大幅上涨",
        505: "60日大幅下跌"
    }
    
    for item in intraday_changes:
        if not item:
            continue
            
        fields = item.split(',')
        if len(fields) >= 7:
            time_str = fields[0]  # 时间
            event_type_code = int(fields[4])  # 事件类型码
            value = fields[5]  # 具体数值
            direction = fields[6]  # 方向标识
            
            # 获取事件类型描述
            event_type_desc = event_type_map.get(event_type_code, f"未知事件({event_type_code})")
            
            # 解析方向
            direction_desc = "买入" if direction == "1" else "卖出" if direction == "2" else "未知"
            

            formatted_item = {
                '时间': time_str,
                '事件类型': event_type_desc,
                '具体数值': value,
                '方向': direction_desc
            }
            
            formatted_data.append(formatted_item)
    
    return formatted_data


def register_kline_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册K线数据相关工具

    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

    @app.tool()
    def get_xueqiu_klines(
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d"
    ) -> str:
        """
        获取指定股票在指定日期范围内的 K 线数据（雪球 API），支持 A 股、B 股、H 股、大盘。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            雪球 K 线数据的 Markdown 表格，含估值、北向/南向资金等扩展字段

        Examples:
            - get_xueqiu_klines("300750.SZ", "2024-01-01", "2024-01-31")
            - get_xueqiu_klines("300750.SZ", "2024-10-01", "2024-10-31", "w")
        """
        try:
            logger.info(
                f"获取雪球K线: {stock_code}, {start_date} 至 {end_date}, 频率: {frequency}"
            )

            raw_klines = data_source.get_xueqiu_klines(
                stock_code, start_date, end_date, frequency
            )

            if not raw_klines:
                return (
                    f"未找到股票代码 '{stock_code}' 在 {start_date} 至 {end_date} "
                    f"的雪球K线数据"
                )

            formatted_data = format_kline_data(raw_klines)
            return format_kline_markdown(stock_code, formatted_data, frequency)

        except Exception as e:
            logger.error(f"获取雪球K线时出错: {e}")
            return f"获取雪球K线失败: {str(e)}"

    @app.tool()
    def get_eastmoney_klines(
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d"
    ) -> str:
        """
        获取指定股票在指定日期范围内的 K 线数据（东方财富 API），支持 A 股、B 股、H 股、大盘。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            东方财富 K 线数据的 Markdown 表格

        Examples:
            - get_eastmoney_klines("300750.SZ", "2024-01-01", "2024-01-31")
            - get_eastmoney_klines("300750.SZ", "2024-10-01", "2024-10-31", "w")
        """
        try:
            logger.info(
                f"获取东方财富K线: {stock_code}, {start_date} 至 {end_date}, 频率: {frequency}"
            )

            raw_klines = data_source.get_eastmoney_klines(
                stock_code, start_date, end_date, frequency
            )

            if not raw_klines:
                return (
                    f"未找到股票代码 '{stock_code}' 在 {start_date} 至 {end_date} "
                    f"的东方财富K线数据"
                )

            formatted_data = format_eastmoney_kline_data(raw_klines)
            return format_eastmoney_kline_markdown(stock_code, formatted_data, frequency)

        except Exception as e:
            logger.error(f"获取东方财富K线时出错: {e}")
            return f"获取东方财富K线失败: {str(e)}"

    @app.tool()
    def get_technical_indicators(
        stock_code: str,
        page_size: int = 30
    ) -> str:
        """
        获取指定股票的技术指标数据，包括MACD、KDJ、RSI、BOLL等技术指标和技术分析。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
            page_size: 返回数据条数，默认为30条

        Returns:
            技术指标数据的Markdown表格

        Examples:
            - get_technical_indicators("300750.SZ")
            - get_technical_indicators("300750.SZ", 20)
        """
        try:
            logger.info(f"获取技术指标: {stock_code}, 条数: {page_size}")

            # 从数据源获取技术指标数据
            raw_technical_data = data_source.get_technical_indicators(stock_code, page_size)
            
            if not raw_technical_data:
                return f"未找到股票代码 '{stock_code}' 的技术指标数据"
            
            # 格式化数据
            formatted_data = format_technical_indicators_data(raw_technical_data)
            stock_name = (
                raw_technical_data[0].get("SECURITY_NAME_ABBR", "")
                if raw_technical_data
                else ""
            )
            return format_technical_indicators_markdown(
                stock_code, stock_name, formatted_data
            )

        except Exception as e:
            logger.error(f"获取技术指标时出错: {e}")
            return f"获取技术指标失败: {str(e)}"

    @app.tool()
    def get_intraday_changes(
        stock_code: str,
    ) -> str:
        """
        获取指定股票的分时图盘口异动数据，包括重要交易事件和异常波动信息。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ

        Returns:
            分时图盘口异动数据的Markdown表格

        Examples:
            - get_intraday_changes("300750.SZ")
        """
        try:
            # 从数据源获取原始数据
            raw_intraday_changes = data_source.get_intraday_changes(stock_code)

            if not raw_intraday_changes:
                return f"未找到股票代码 '{stock_code}' 的分时图盘口异动数据"

            # 格式化数据
            formatted_data = format_intraday_changes_data(raw_intraday_changes)

            # 生成Markdown表格
            return format_markdown_report(
                f"{stock_code} 分时图盘口异动数据",
                table_data=formatted_data,
            )

        except Exception as e:
            logger.error(f"获取分时图盘口异动时出错: {e}")
            return f"获取分时图盘口异动失败: {str(e)}"
