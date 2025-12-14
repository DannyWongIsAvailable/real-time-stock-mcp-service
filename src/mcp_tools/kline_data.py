"""
K线数据工具
src/mcp_tools/kline_data.py
提供K线数据查询和分析功能
"""
import logging
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from ..data_source_interface import FinancialDataInterface
from ..utils.utils import format_number, format_large_number
from ..utils.markdown_formatter import format_list_to_markdown_table

logger = logging.getLogger(__name__)


def parse_kline_data(klines: List[str]) -> List[Dict]:
    """
    解析K线原始数据字符串

    Args:
        klines: K线原始数据字符串列表

    Returns:
        解析后的K线数据字典列表
    """
    result = []
    for kline in klines:
        fields = kline.split(",")
        if len(fields) >= 11:
            result.append({
                "date": fields[0],           # 日期
                "open": float(fields[1]),    # 开盘
                "close": float(fields[2]),   # 收盘
                "high": float(fields[3]),    # 最高
                "low": float(fields[4]),     # 最低
                "volume": int(fields[5]),    # 成交量
                "amount": float(fields[6]),  # 成交额
                "amplitude": float(fields[7]), # 振幅
                "change_percent": float(fields[8]), # 涨跌幅
                "change_amount": float(fields[9]),  # 涨跌额
                "turnover_rate": float(fields[10])  # 换手率
            })
    return result


def register_kline_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册K线数据相关工具

    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

    @app.tool()
    def get_kline(
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d"
    ) -> str:
        """
        获取指定股票在指定日期范围内的K线数据，支持A股，H股，大盘。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            K线数据的Markdown表格

        Examples:
            - get_kline("300750.SZ", "2024-01-01", "2024-01-31")
            - get_kline("300750.SZ", "2024-10-01", "2024-10-31", "w")
        """
        try:
            logger.info(f"获取K线: {stock_code}, {start_date} 至 {end_date}, 频率: {frequency}")

            # 从数据源获取原始数据
            raw_klines = data_source.get_historical_k_data(stock_code, start_date, end_date, frequency)

            if not raw_klines:
                return f"未找到股票代码 '{stock_code}' 在 {start_date} 至 {end_date} 的K线数据"

            # 解析原始数据
            kline_data = parse_kline_data(raw_klines)

            # 格式化数据
            formatted_data = []
            for k in kline_data:
                open_price = k.get('open', 0)
                close_price = k.get('close', 0)
                high_price = k.get('high', 0)
                low_price = k.get('low', 0)
                volume = k.get('volume', 0)
                amount = k.get('amount', 0)
                change_pct = k.get('change_percent', 0)
                amplitude = k.get('amplitude', 0)
                change_amount = k.get('change_amount', 0)
                turnover_rate = k.get('turnover_rate', 0)

                # 计算 K 线状态
                if close_price > open_price:
                    status = "上涨（阳线）"
                elif close_price < open_price:
                    status = "下跌（阴线）"
                else:
                    status = "平盘（十字星）"

                formatted_data.append({
                    '日期': k.get('date', ''),
                    'K线状态': status,
                    '开盘': format_number(open_price),
                    '收盘': format_number(close_price),
                    '最高': format_number(high_price),
                    '最低': format_number(low_price),
                    '涨跌幅': f"{'+' if change_pct > 0 else ''}{change_pct:.2f}%",
                    '成交量': format_large_number(volume),
                    '成交额': format_large_number(amount),
                    '振幅': f"{amplitude:.2f}%",
                    '涨跌额': format_number(change_amount),
                    '换手率': f"{turnover_rate:.2f}%"
                })

            table = format_list_to_markdown_table(formatted_data)
            note = f"\n\n💡 显示 {len(formatted_data)} 条K线数据，频率: {frequency}"
            return f"## {stock_code} K线数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"获取K线时出错: {e}")
            return f"获取K线失败: {str(e)}"

