"""
实时股票数据 MCP 工具
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from stock_mcp.data_source_interface import FinancialDataInterface
from stock_mcp.utils.markdown_formatter import (
    format_list_to_markdown_table,
    format_markdown_report,
)
from stock_mcp.utils.utils import format_large_number, format_number

logger = logging.getLogger(__name__)

_CN_TZ = timezone(timedelta(hours=8))

QUOTE_LABELS = {
    "symbol": "代码",
    "code": "证券代码",
    "name": "名称",
    "exchange": "交易所",
    "current": "现价",
    "current_ext": "现价(扩展)",
    "open": "开盘",
    "high": "最高",
    "low": "最低",
    "last_close": "昨收",
    "chg": "涨跌额",
    "percent": "涨跌幅",
    "amplitude": "振幅",
    "volume": "成交量",
    "volume_ext": "成交量(扩展)",
    "amount": "成交额",
    "turnover_rate": "换手率",
    "volume_ratio": "量比",
    "avg_price": "均价",
    "limit_up": "涨停价",
    "limit_down": "跌停价",
    "high52w": "52周最高",
    "low52w": "52周最低",
    "market_capital": "总市值",
    "float_market_capital": "流通市值",
    "float_shares": "流通股本",
    "total_shares": "总股本",
    "pe_ttm": "市盈率(TTM)",
    "pe_lyr": "市盈率(静)",
    "pe_forecast": "市盈率(预测)",
    "pb": "市净率",
    "eps": "每股收益",
    "navps": "每股净资产",
    "dividend": "股息",
    "dividend_yield": "股息率",
    "profit": "净利润",
    "profit_four": "四季度利润",
    "profit_forecast": "预测利润",
    "currency": "货币",
    "timestamp": "行情时间",
    "time": "时间戳",
    "timestamp_ext": "行情时间(扩展)",
    "status": "交易状态",
    "type": "类型",
    "sub_type": "子类型",
    "tick_size": "最小报价单位",
    "lot_size": "每手股数",
    "delayed": "延迟行情",
    "current_year_percent": "年初至今涨跌幅",
    "issue_date": "上市日期",
    "pledge_ratio": "质押比例",
    "goodwill_in_net_assets": "商誉占净资产比",
    "is_registration": "是否注册制",
    "is_registration_desc": "注册制说明",
    "weighted_voting_rights": "同股同权",
    "weighted_voting_rights_desc": "同股同权说明",
    "is_vie": "VIE结构",
    "is_vie_desc": "VIE说明",
    "no_profit": "是否未盈利",
    "no_profit_desc": "未盈利说明",
    "security_status": "证券状态",
    "lock_set": "限售",
    "traded_amount_ext": "成交额(扩展)",
}

MARKET_LABELS = {
    "status": "市场状态",
    "status_id": "状态ID",
    "region": "地区",
    "time_zone": "时区",
    "time_zone_desc": "时区说明",
    "delay_tag": "延迟标记",
    "downgrade_night_session": "夜盘降级",
    "daylight_savings": "夏令时",
}

OTHERS_LABELS = {
    "pankou_ratio": "盘口比",
    "cyb_switch": "创业板开关",
}


def _format_nullable(value: Any, formatter) -> str:
    if value is None:
        return "-"
    return formatter(value)


def _format_timestamp_ms(value: Any) -> str:
    if value is None:
        return "-"
    try:
        ts = int(value) / 1000
        return datetime.fromtimestamp(ts, tz=_CN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return str(value)


def _format_quote_value(key: str, value: Any) -> str:
    if value is None:
        return "-"
    if key in ("timestamp", "time", "timestamp_ext", "issue_date"):
        return _format_timestamp_ms(value)
    if key in ("volume", "volume_ext", "float_shares", "total_shares"):
        return format_large_number(int(value))
    if key in (
        "amount", "market_capital", "float_market_capital",
        "profit", "profit_four", "profit_forecast",
    ):
        return format_large_number(float(value))
    if key in ("percent", "turnover_rate", "amplitude", "dividend_yield", "current_year_percent"):
        return f"{float(value):.2f}%"
    if key in ("pe_ttm", "pe_lyr", "pe_forecast", "pb", "volume_ratio"):
        return f"{float(value):.4f}"
    if key in ("eps", "navps"):
        return format_number(float(value))
    if key in ("current", "open", "high", "low", "last_close", "chg", "avg_price", "limit_up", "limit_down", "high52w", "low52w", "dividend"):
        return format_number(float(value))
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def _dict_to_rows(data: Dict[str, Any], labels: Dict[str, str]) -> List[Dict[str, str]]:
    rows = []
    for key, label in labels.items():
        if key in data:
            rows.append({"字段": label, "值": _format_quote_value(key, data[key])})
    for key, value in data.items():
        if key not in labels:
            rows.append({"字段": key, "值": _format_quote_value(key, value)})
    return rows


def format_real_time_data(data: Dict[str, Any]) -> str:
    """将雪球 quote.json 的 data 格式化为 Markdown"""
    quote = data.get("quote") or {}
    market = data.get("market") or {}
    others = data.get("others") or {}
    tags = data.get("tags") or []

    name = quote.get("name", "")
    code = quote.get("code", "")
    symbol = quote.get("symbol", "")
    title = f"{name}({code}.{quote.get('exchange', '')}) 实时行情 [{symbol}]"

    sections: List[tuple[str, str]] = []

    if quote:
        sections.append(
            ("报价", format_list_to_markdown_table(_dict_to_rows(quote, QUOTE_LABELS)))
        )

    if market:
        sections.append(
            ("市场", format_list_to_markdown_table(_dict_to_rows(market, MARKET_LABELS)))
        )

    if others:
        sections.append(
            ("其它", format_list_to_markdown_table(_dict_to_rows(others, OTHERS_LABELS)))
        )

    if tags:
        tag_rows = [
            {"标签": t.get("description", ""), "值": str(t.get("value", ""))}
            for t in tags
        ]
        sections.append(("标签", format_list_to_markdown_table(tag_rows)))

    return format_markdown_report(title, sections=sections)


def register_real_time_data_tools(app: FastMCP, data_source: FinancialDataInterface):
    """注册实时股票数据工具"""

    @app.tool()
    def get_real_time_data(symbol: str) -> str:
        """
        获取指定股票的实时股票数据，包括价格、涨跌幅、成交量等信息。

        Args:
            symbol: 股票代码，数字后带上交易所代码，格式如688041.SH

        Returns:
            格式化的实时股票数据，以Markdown表格形式展示

        Examples:
            - get_real_time_data("688041.SH")
        """
        try:
            logger.info(f"获取实时股票数据: {symbol}")

            data = data_source.get_real_time_data(symbol)
            if not data or not data.get("quote"):
                return f"未找到股票 '{symbol}' 的实时行情数据"

            return format_real_time_data(data)

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_real_time_market_indices() -> str:
        """
        获取实时大盘指数数据，包括上证指数、深证成指、创业板指等的实时行情。

        Returns:
            格式化的实时大盘指数数据，以Markdown表格形式展示

        Examples:
            - get_real_time_market_indices()
        """
        try:
            logger.info("获取实时大盘指数数据")

            indices_data = data_source.get_real_time_market_indices()
            if not indices_data:
                return "未找到数据"

            formatted_data = []
            for index_data in indices_data:
                formatted_data.append({
                    "指数代码": index_data.get("f12", "N/A"),
                    "指数名称": index_data.get("f14", "N/A"),
                    "当前点位": f"{index_data.get('f2', 0) / 100:.2f}",
                    "涨跌点数": f"{index_data.get('f4', 0) / 100:.2f}",
                    "涨跌幅": f"{index_data.get('f3', 0) / 100:.2f}%",
                })

            return format_markdown_report(
                "实时大盘指数数据",
                table_data=formatted_data,
            )

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    logger.info("实时股票数据工具已注册")
