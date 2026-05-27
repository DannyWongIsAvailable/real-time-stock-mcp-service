"""
智能点评MCP工具
src/mcp_tools/smart_review.py
提供股票智能点评相关的MCP工具
"""

import logging
from mcp.server.fastmcp import FastMCP

from stock_mcp.data_source_interface import FinancialDataInterface
from stock_mcp.utils.markdown_formatter import format_list_to_markdown_table, format_markdown_report

logger = logging.getLogger(__name__)


def register_smart_review_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册智能点评相关工具
    
    Args:
        server: MCP服务器实例
        data_source: 数据源实例
    """
    @app.tool()
    def get_participation_wish(stock_code: str) -> str:
        """
        获取个股市场参与意愿数据

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
        Examples:
            - get_participation_wish("300750.SZ")
        """
        try:
            # 调用数据源获取市场参与意愿数据
            wish_data = data_source.get_participation_wish(stock_code)
            
            if not wish_data:
                return "未找到相关市场参与意愿数据"
            
            # 处理错误情况
            if isinstance(wish_data, list) and len(wish_data) > 0 and "error" in wish_data[0]:
                return f"获取市场参与意愿数据失败: {wish_data[0]['error']}"

            # 准备表格数据
            table_data = []
            for item in wish_data:
                formatted_item = {
                    "交易日期": item.get("TRADE_DATE", "").split(" ")[0],
                    "当日参与意愿度": f"{item.get('PARTICIPATION_WISH', 0):.2f}",
                    "5日平均意愿度": f"{item.get('PARTICIPATION_WISH_5DAYS', 0):.2f}",
                    "当日意愿度变化": f"{item.get('PARTICIPATION_WISH_CHANGE', 0):+.2f}",
                    "5日平均意愿变化": f"{item.get('PARTICIPATION_WISH_5DAYSCHANGE', 0):+.2f}",
                }
                table_data.append(formatted_item)
            
            security_name = stock_code

            return format_markdown_report(
                f"{security_name} 市场参与意愿",
                table_data=table_data,
                footnote=(
                    "说明：参与意愿由大数据对投资者入场意愿量化统计得出，"
                    "参与意愿上升代表入场意愿增强"
                ),
            )
        except Exception as e:
            logger.error(f"获取市场参与意愿数据失败: {e}")
            return f"获取市场参与意愿数据失败: {e}"

    @app.tool()
    def get_main_force_control(stock_code: str) -> str:
        """
        获取个股主力控盘数据

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
        Examples:
            - get_main_force_control("300750.SZ")
        """
        try:
            # 调用数据源获取主力控盘数据
            control_data = data_source.get_main_force_control(stock_code)
            
            if not control_data:
                return "未找到相关主力控盘数据"
            
            # 处理错误情况
            if isinstance(control_data, list) and len(control_data) > 0 and "error" in control_data[0]:
                return f"获取主力控盘数据失败: {control_data[0]['error']}"

            # 准备表格数据
            table_data = []
            for item in control_data:
                formatted_item = {
                    "收盘价": f"{item.get('CLOSE_PRICE', 0):.2f}",
                    "涨跌幅": f"{item.get('CHANGE_RATE', 0):+.2f}%",
                    "换手率": f"{item.get('TURNOVERRATE', 0):.2f}%",
                    "机构参与度": f"{item.get('ORG_PARTICIPATE', 0) * 100:.2f}%",
                    "控盘状态": item.get("PARTICIPATE_TYPE_CN", ""),
                    "近1日成本价": f"{item.get('PRIME_COST', 0):.2f}",
                    "20日成本": f"{item.get('PRIME_COST_20DAYS', 0):.2f}",
                    "60日成本": f"{item.get('PRIME_COST_60DAYS', 0):.2f}",
                    "交易日期": item.get("TRADE_DATE", "").split(" ")[0],
                }
                table_data.append(formatted_item)
            
            latest = control_data[-1]
            stock_name = latest["SECURITY_NAME_ABBR"]
            footnote = (
                f"点评：机构参与度为{latest['ORG_PARTICIPATE'] * 100:.2f}%，"
                f"属于{latest['PARTICIPATE_TYPE_CN']}；"
                f"最近1日主力成本{latest['PRIME_COST']:.2f}元，"
                f"最近20日主力成本{latest['PRIME_COST_20DAYS']:.2f}元"
            )

            return format_markdown_report(
                f"{stock_name} 主力控盘数据",
                table_data=table_data,
                footnote=footnote,
            )
        except Exception as e:
            logger.error(f"获取主力控盘数据失败: {e}")
            return f"获取主力控盘数据失败: {e}"

    @app.tool()
    def get_smart_score(stock_code: str) -> str:
        """
        获取股票智能评分数据

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
        Examples:
            - get_smart_score("300750.SZ")
        """
        try:
            # 调用数据源获取智能评分数据
            score_data = data_source.get_smart_score(stock_code)


            table_data = [
                {"字段": "股票代码", "值": score_data.get("SECUCODE", stock_code)},
                {"字段": "股票名称", "值": score_data.get("SECURITY_NAME_ABBR", stock_code)},
                {"字段": "评分", "值": f"{score_data.get('TOTAL_SCORE', 0):.2f}"},
                {"字段": "评分变化", "值": f"{score_data.get('TOTAL_SCORE_CHANGE', 0):+.2f}"},
                {"字段": "次日上涨概率", "值": f"{score_data.get('RISE_1_PROBABILITY', 0):.2f}%"},
                {"字段": "次日平均涨跌", "值": f"{score_data.get('AVERAGE_1_INCREASE', 0):.2f}%"},
                {"字段": "五日上涨概率", "值": f"{score_data.get('RISE_5_PROBABILITY', 0):.2f}%"},
                {"字段": "五日平均涨跌", "值": f"{score_data.get('AVERAGE_5_INCREASE', 0):.2f}%"},
                {"字段": "分析时间", "值": score_data.get("DIAGNOSE_TIME", "")},
            ]
            explain = (score_data.get("WORDS_EXPLAIN") or "").strip()
            footnote = f"分析解读：{explain}" if explain else None

            return format_markdown_report(
                f"{score_data.get('SECURITY_NAME_ABBR', stock_code)} 智能评分",
                table_data=table_data,
                footnote=footnote,
            )
        except Exception as e:
            logger.error(f"获取股票智能评分数据失败: {e}")
            return f"获取股票智能评分数据失败 {e}"

    @app.tool()
    def get_smart_score_rank(stock_code: str) -> str:
        """
        获取个股智能评分排名数据

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
        Examples:
            - get_smart_score_rank("300750.SZ")

        """
        try:
            # 调用数据源获取智能评分排名数据
            rank_data = data_source.get_smart_score_rank(stock_code)
            
            if not rank_data:
                return "未找到相关评分排名数据"

            sections = [
                (
                    "基本信息",
                    format_list_to_markdown_table(
                        [
                            {
                                "字段": "股票代码",
                                "值": rank_data.get("SECUCODE", stock_code),
                            },
                            {
                                "字段": "股票名称",
                                "值": rank_data.get("SECURITY_NAME_ABBR", ""),
                            },
                            {
                                "字段": "所属板块",
                                "值": (
                                    f"{rank_data.get('BOARD_NAME', '')}"
                                    f"({rank_data.get('BOARD_CODE', '')})"
                                ),
                            },
                            {
                                "字段": "交易日期",
                                "值": rank_data.get("TRADE_DATE", "").split(" ")[0],
                            },
                        ]
                    ),
                ),
                (
                    "综合评分",
                    format_list_to_markdown_table(
                        [
                            {
                                "字段": "综合评分",
                                "值": f"{rank_data.get('COMPRE_SCORE', 0):.2f}分",
                            },
                            {
                                "字段": "当日涨跌幅",
                                "值": f"{rank_data.get('CHANGE_RATE', 0):+.2f}%",
                            },
                        ]
                    ),
                ),
                (
                    "行业内排名",
                    format_list_to_markdown_table(
                        [
                            {
                                "字段": "行业排名",
                                "值": f"第{rank_data.get('INDUSTRY_RANK', 0)}名",
                            },
                            {
                                "字段": "行业最高分",
                                "值": f"{rank_data.get('INDUSTRY_SCORE_HIGH', 0):.2f}分",
                            },
                            {
                                "字段": "行业平均分",
                                "值": f"{rank_data.get('INDUSTRY_SCORE_AVG', 0):.2f}分",
                            },
                            {
                                "字段": "行业最低分",
                                "值": f"{rank_data.get('INDUSTRY_SCORE_LOW', 0):.2f}分",
                            },
                            {
                                "字段": "行业统计",
                                "值": (
                                    f"{rank_data.get('BOARD_NAME', '')}行业共"
                                    f"{rank_data.get('INDUSTRY_STOCK_NUM', 0)}只股票，"
                                    f"已评{rank_data.get('EVALUATE_INDUSTRY_NUM', 0)}只"
                                ),
                            },
                        ]
                    ),
                ),
                (
                    "全市场排名",
                    format_list_to_markdown_table(
                        [
                            {
                                "字段": "市场排名",
                                "值": f"第{rank_data.get('MARKET_RANK', 0)}名",
                            },
                            {
                                "字段": "战胜比例",
                                "值": f"打败了市场{rank_data.get('STOCK_RANK_RATIO', 0):.2f}%的股票",
                            },
                            {
                                "字段": "市场最高分",
                                "值": f"{rank_data.get('MARKET_SCORE_HIGH', 0):.2f}分",
                            },
                            {
                                "字段": "市场平均分",
                                "值": f"{rank_data.get('MARKET_SCORE_AVG', 0):.2f}分",
                            },
                            {
                                "字段": "市场最低分",
                                "值": f"{rank_data.get('MARKET_SCORE_LOW', 0):.2f}分",
                            },
                            {
                                "字段": "市场统计",
                                "值": (
                                    f"沪深市场共{rank_data.get('MARKET_STOCK_NUM', 0)}只股票，"
                                    f"已评{rank_data.get('EVALUATE_MARKET_NUM', 0)}只"
                                ),
                            },
                        ]
                    ),
                ),
            ]

            return format_markdown_report(
                f"{rank_data.get('SECURITY_NAME_ABBR', stock_code)} 智能评分排名",
                sections=sections,
            )
        except Exception as e:
            logger.error(f"获取个股智能评分排名数据失败: {e}")
            return f"获取个股智能评分排名数据失败: {e}"

    @app.tool()
    def get_top_rated_stocks(page_size: int = 10) -> str:
        """
        获取全市场高评分个股

        Args:
            page_size:  返回排名前几条
        Examples:
            get_top_rated_stocks(10)
        """
        try:
            # 调用数据源获取全市场高评分个股数据
            stocks_data = data_source.get_top_rated_stocks(page_size)
            
            if not stocks_data:
                return "未找到相关高评分个股数据"
            
            # 处理错误情况
            if isinstance(stocks_data, list) and len(stocks_data) > 0 and "error" in stocks_data[0]:
                return f"获取全市场高评分个股数据失败: {stocks_data[0]['error']}"


            evaluate_market_num = stocks_data[0].get("EVALUATE_MARKET_NUM", 0)
            market_score_high = stocks_data[0].get("MARKET_SCORE_HIGH", 0)
            market_score_low = stocks_data[0].get("MARKET_SCORE_LOW", 0)
            market_score_avg = stocks_data[0].get("MARKET_SCORE_AVG", 0)

            # 准备表格数据
            table_data = []
            for stock in stocks_data:
                formatted_stock = {
                    "排名": stock.get("MARKET_RANK", ""),
                    "股票代码": stock.get("SECURITY_CODE", ""),
                    "股票名称": stock.get("SECURITY_NAME_ABBR", ""),
                    "所属板块": stock.get("BOARD_NAME", ""),
                    "综合评分": f"{stock.get('COMPRE_SCORE', 0):.2f}",
                    "当日涨跌幅": f"{stock.get('CHANGE_RATE', 0):+.2f}%",
                }
                table_data.append(formatted_stock)
            
            return format_markdown_report(
                "全市场高评分个股排行榜",
                table_data=table_data,
                footnote=(
                    f"全市场参与评分的股票数量：{evaluate_market_num}；"
                    f"市场最高分：{market_score_high:.2f}分；"
                    f"市场最低分：{market_score_low:.2f}分；"
                    f"市场平均分：{market_score_avg:.2f}分"
                ),
            )
        except Exception as e:
            logger.error(f"获取全市场高评分个股数据失败: {e}")
            return f"获取全市场高评分个股数据失败: {e}"