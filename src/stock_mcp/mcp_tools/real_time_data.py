"""
实时股票数据 MCP 工具

提供实时股票数据查询功能
"""

import logging
from mcp.server.fastmcp import FastMCP
from stock_mcp.data_source_interface import FinancialDataInterface
from stock_mcp.utils.markdown_formatter import format_list_to_markdown_table
from stock_mcp.utils.utils import format_large_number

logger = logging.getLogger(__name__)


def register_real_time_data_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册实时股票数据工具

    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

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

            # 1. 使用data_source获取数据
            data = data_source.get_real_time_data(symbol)

            # 2. 处理数据
            if not data:
                return "未找到数据"

            # 3. 解析东方财富返回的数据格式
            # 提取k线数据
            klines = data.get("klines", [])
            if not klines:
                return "未找到有效数据"
                
            # 解析最新的K线数据（通常只有一条）
            latest_kline = klines[0].split(",")
            if len(latest_kline) < 11:
                return "数据格式错误"
                
            # 根据东方财富的数据格式解析
            date = latest_kline[0]
            open_price = float(latest_kline[1])
            close_price = float(latest_kline[2])
            high_price = float(latest_kline[3])
            low_price = float(latest_kline[4])
            volume = int(latest_kline[5])
            amount = float(latest_kline[6])
            amplitude_pct = float(latest_kline[7])   # 振幅%
            change_pct = float(latest_kline[8])      # 涨跌幅%
            change_amount = float(latest_kline[9])   # 涨跌额
            turnover_rate = float(latest_kline[10])  # 换手率%
            
            # 计算其他衍生数据
            pre_close = float(data.get("preKPrice", close_price - change_amount))  # 昨收价
            
            # 格式化显示数据
            formatted_data = {
                "股票名称": data.get("name", "N/A"),
                "股票代码": data.get("code", "N/A"),
                "当前价格": f"{close_price:.2f}元",
                "涨跌额": f"{change_amount:.2f}元",
                "涨跌幅": f"{change_pct:.2f}%",
                "开盘价": f"{open_price:.2f}元",
                "最高价": f"{high_price:.2f}元",
                "最低价": f"{low_price:.2f}元",
                "昨收价": f"{pre_close:.2f}元",
                "成交量": f"{format_large_number(volume)}",
                "成交额": f"{format_large_number(amount)}元",
                "振幅": f"{amplitude_pct:.2f}%",
                "换手率": f"{turnover_rate:.2f}%",
                "更新时间": date
            }

            # 4. 直接格式化为Markdown
            result = "实时股票数据\n\n"
            for key, value in formatted_data.items():
                result += f"- {key}: {value}\n"
            
            return result

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

            # 1. 使用data_source获取数据
            indices_data = data_source.get_real_time_market_indices()

            # 2. 处理数据
            if not indices_data:
                return "未找到数据"

            # 3. 解包并格式化数据为表格
            formatted_data = []
            
            for index_data in indices_data:
                # 提取并格式化关键信息
                name = index_data.get("f14", "N/A")  # 指数名称
                code = index_data.get("f12", "N/A")  # 指数代码
                point = index_data.get("f2", 0) / 100  # 指数点位
                change_percent = index_data.get("f3", 0) / 100  # 涨跌幅(%)
                change_point = index_data.get("f4", 0) / 100  # 涨跌点数

                formatted_data.append({
                    "指数代码": code,
                    "指数名称": name,
                    "当前点位": f"{point:.2f}",
                    "涨跌点数": f"{change_point:.2f}",
                    "涨跌幅": f"{change_percent:.2f}%"
                })

            # 使用format_list_to_markdown_table格式化为表格
            table = format_list_to_markdown_table(formatted_data)
            
            result = "**实时大盘指数数据**\n\n"
            result += table
            
            return result

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    logger.info("实时股票数据工具已注册")