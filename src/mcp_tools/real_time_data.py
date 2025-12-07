"""
实时股票数据 MCP 工具

提供实时股票数据查询功能
"""

import logging
from mcp.server.fastmcp import FastMCP
from src.data_source_interface import FinancialDataInterface
from src.utils.utils import format_timestamp

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
        获取实时股票数据

        获取指定股票的实时行情数据，包括价格、涨跌幅、成交量等信息。

        Args:
            symbol: 股票代码，A股必须在前面加上交易所代码，格式如 SZ300750  或 SH600519，H股只用数字

        Returns:
            格式化的实时股票数据，以Markdown表格形式展示

        Examples:
            - get_real_time_data("SZ300750")
            - get_real_time_data("SH600519")
            - get_real_time_data("01810")
        """
        try:
            logger.info(f"获取实时股票数据: {symbol}")

            # 1. 使用data_source获取数据
            data = data_source.get_real_time_data(symbol)

            # 2. 处理数据
            if not data:
                return "未找到数据"

            # 3. 解包并格式化数据
            quote = data.get("quote", {})
            market = data.get("market", {})
            
            # 提取并格式化关键信息
            formatted_data = {
                "股票名称": quote.get("name", "N/A"),
                "股票代码": quote.get("symbol", "N/A"),
                "当前价格": f"{quote.get('current', 'N/A')}元",
                "涨跌额": f"{quote.get('chg', 'N/A')}元",
                "涨跌幅": f"{quote.get("percent", "N/A")}%",
                "开盘价": f"{quote.get('open', 'N/A')}元",
                "最高价": f"{quote.get('high', 'N/A')}元",
                "最低价": f"{quote.get('low', 'N/A')}元",
                "昨收价": f"{quote.get('last_close', 'N/A')}元",
                "成交量": quote.get("volume", "N/A"),
                "成交额": f"{quote.get('amount', 'N/A')}元",
                "换手率": f"{quote.get("turnover_rate", "N/A")}%",
                "量比": quote.get("volume_ratio", "N/A"),
                "市值": f"{quote.get('market_capital', 'N/A')}元",
                "市盈率(TTM)": quote.get("pe_ttm", "N/A"),
                "市净率": quote.get("pb", "N/A"),
                "市盈率(静)": quote.get("pe_lyr", "N/A"),
                "市盈率(动)": quote.get("pe_forecast", "N/A"),
                "交易状态": market.get("status", "N/A"),
                "更新时间": format_timestamp(quote.get("timestamp")),
                "流通股本": quote.get("float_shares", "N/A"),
                "总股本": quote.get("total_shares", "N/A"),
                "流通市值": f"{quote.get('float_market_capital', 'N/A')}元",
                "涨跌停价": f"涨停 {quote.get('limit_up', 'N/A')}元 / 跌停 {quote.get('limit_down', 'N/A')}元",
                "52周最高": f"{quote.get('high52w', 'N/A')}元",
                "52周最低": f"{quote.get('low52w', 'N/A')}元",
                "振幅": f"{quote.get("amplitude", "N/A")}%",
                "均价": f"{quote.get('avg_price', 'N/A')}元",
                "年内涨跌幅": f"{quote.get("current_year_percent", "N/A")}%",
                "每股收益": f"{quote.get('eps', 'N/A')}元",
                "股息": f"{quote.get('dividend', 'N/A')}元",
                "股息率": f"{quote.get("dividend_yield", "N/A")}%",
                "每股净资产": quote.get("navps", "N/A"),
                "质押率": f"{quote.get("pledge_ratio", "N/A")}%",
                "是否盈利": quote.get("no_profit_desc", "N/A"),
                "是否注册制": quote.get("is_registration_desc", "N/A"),
                "是否VIE架构": quote.get("is_vie_desc", "N/A")
            }

            # 4. 直接格式化为Markdown，不使用format_dict_to_markdown函数
            result = "**实时股票数据**\n\n"
            for key, value in formatted_data.items():
                result += f"- **{key}**: {value}\n"
            
            # 添加标签信息
            tags = data.get("tags", [])
            if tags:
                tag_descriptions = [tag.get("description", "") for tag in tags]
                result += f"\n**标签**: {', '.join(tag_descriptions)}"
            
            return result

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    logger.info("实时股票数据工具已注册")

