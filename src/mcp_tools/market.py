"""
市场行情 MCP 工具

提供行情数据查询功能
"""

import logging
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from src.data_source_interface import FinancialDataInterface
from src.utils.markdown_formatter import format_list_to_markdown_table
from src.utils.utils import format_number, format_large_number

logger = logging.getLogger(__name__)


def register_market_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册市场行情工具

    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

    @app.tool()
    def get_plate_quotation(plate_type: int = 2) -> str:
        """
        获取板块行情数据

        获取东方财富网的涨跌幅前10板块行情数据，包括行业板块、概念板块、地域板块等。

        Args:
            plate_type: 板块类型参数
                - 1: 地域板块  
                - 2: 行业板块 (默认)
                - 3: 概念板块

        Returns:
            格式化的板块行情数据，以Markdown表格形式展示

        Examples:
            - get_plate_quotation()
            - get_plate_quotation(1)
            - get_plate_quotation(3)
        """
        def _format_plate_data(raw_data: List[Dict]) -> List[Dict]:
            """
            格式化板块行情数据

            Args:
                raw_data: 原始板块行情数据

            Returns:
                格式化后的板块行情数据列表
            """
            formatted_data = []

            for item in raw_data:
                # 处理价格类数据（需要除以100）
                latest_price = item.get("f2", 0) / 100 if item.get("f2") else 0
                change_percent = item.get("f3", 0) / 100 if item.get("f3") else 0
                change_amount = item.get("f4", 0) / 100 if item.get("f4") else 0
                turnover_rate = item.get("f8", 0) / 100 if item.get("f8") else 0
                leading_change_percent = item.get("f136", 0) / 100 if item.get("f136") else 0
                declining_change_percent = item.get("f222", 0) / 100 if item.get("f222") else 0

                # 处理总市值（单位转换为亿）
                total_market_value = item.get("f20", 0) / 100000000 if item.get("f20") else 0

                formatted_item = {
                    "板块代码": item.get("f12", ""),
                    "板块名称": item.get("f14", ""),
                    "最新价": f"{latest_price:.2f}",
                    "涨跌幅": f"{'+' if change_percent > 0 else ''}{change_percent:.2f}%",
                    "涨跌额": f"{'+' if change_amount > 0 else ''}{change_amount:.2f}",
                    "换手率": f"{turnover_rate:.2f}%",
                    "总市值(亿)": f"{total_market_value:.2f}",
                    "上涨家数": item.get("f104", 0),
                    "下跌家数": item.get("f105", 0),
                    "领涨股": f"{item.get('f128', '')}({item.get('f140', '')})",
                    "领涨股市场": "沪市" if item.get("f141", 0) == 1 else "深市",
                    "领涨股涨跌幅": f"{'+' if leading_change_percent > 0 else ''}{leading_change_percent:.2f}%",
                    "领跌股": f"{item.get('f207', '')}({item.get('f208', '')})",
                    "领跌股市场": "沪市" if item.get("f209", 0) == 1 else "深市",
                    "领跌股涨跌幅": f"{'+' if declining_change_percent > 0 else ''}{declining_change_percent:.2f}%"
                }

                formatted_data.append(formatted_item)

            return formatted_data

        try:
            logger.info(f"获取板块行情数据: 板块类型={plate_type}")
            
            # 初始化爬虫
            from src.crawler.market import MarketSpider
            spider = MarketSpider()
            
            # 获取原始数据
            raw_data = spider.get_plate_quotation(plate_type)
            
            if not raw_data:
                return "未找到板块行情数据"
            
            # 格式化数据
            formatted_data = _format_plate_data(raw_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            # 添加说明
            plate_type_map = {1: "地域板块", 2: "行业板块", 3: "概念板块"}
            plate_name = plate_type_map.get(plate_type, "未知板块")
            note = f"\n\n💡 显示涨跌幅前10{plate_name}的行情数据"
            
            return f"## {plate_name}涨跌幅前10行情数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_historical_fund_flow(stock_code: str) -> str:
        """
        获取历史资金流向数据

        获取指定股票最近10个交易日的资金流向数据，包括主力资金、散户资金、中单资金等的流入流出情况。

        Args:
            stock_code: 股票代码，数字后带上交易所代码，格式如688041.SH

        Returns:
            格式化的历史资金流向数据，以Markdown表格形式展示

        Examples:
            - get_historical_fund_flow("688041.SH")
        """

        def _format_fund_flow_data(raw_data: Dict) -> List[Dict]:
            """
            格式化资金流向数据

            Args:
                raw_data: 原始资金流向数据

            Returns:
                格式化后的资金流向数据列表
            """
            formatted_data = []

            
            klines = raw_data.get("klines", [])
            
            # 反向遍历，使最新的数据显示在前面
            for line in reversed(klines):
                parts = line.split(",")
                
                # 解析各个字段
                date = parts[0]
                main_net_inflow_amount = round(float(parts[1]), 2)  # 主力净流入_净额
                retail_net_inflow_amount = round(float(parts[2]), 2)  # 小单净流入_净额
                medium_net_inflow_amount = round(float(parts[3]), 2)  # 中单净流入_净额
                large_net_inflow_amount = round(float(parts[4]), 2)  # 大单净流入_净额
                super_large_net_inflow_amount = round(float(parts[5]), 2)  # 超大单净流入_净额
                main_net_inflow_ratio = round(float(parts[6]), 2)  # 主力净流入_净占比
                retail_net_inflow_ratio = round(float(parts[7]), 2)  # 小单净流入_净占比
                medium_net_inflow_ratio = round(float(parts[8]), 2)  # 中单净流入_净占比
                large_net_inflow_ratio = round(float(parts[9]), 2)  # 大单净流入_净占比
                super_large_net_inflow_ratio = round(float(parts[10]), 2)  # 超大单净流入_净占比
                closing_price = round(float(parts[11]), 2)  # 收盘价
                change_percent = round(float(parts[12]), 2)  # 涨跌幅
                
                formatted_item = {
                    "日期": date,
                    "收盘价": closing_price,
                    "涨跌幅": f"{'+' if change_percent >= 0 else ''}{change_percent}%",
                    "主力净流入_净额": format_large_number(main_net_inflow_amount),
                    "主力净流入_净占比": f"{'+' if main_net_inflow_ratio >= 0 else ''}{main_net_inflow_ratio}%",
                    "超大单净流入_净额": format_large_number(super_large_net_inflow_amount),
                    "超大单净流入_净占比": f"{'+' if super_large_net_inflow_ratio >= 0 else ''}{super_large_net_inflow_ratio}%",
                    "大单净流入_净额": format_large_number(large_net_inflow_amount),
                    "大单净流入_净占比": f"{'+' if large_net_inflow_ratio >= 0 else ''}{large_net_inflow_ratio}%",
                    "中单净流入_净额": format_large_number(medium_net_inflow_amount),
                    "中单净流入_净占比": f"{'+' if medium_net_inflow_ratio >= 0 else ''}{medium_net_inflow_ratio}%",
                    "小单净流入_净额": format_large_number(retail_net_inflow_amount),
                    "小单净流入_净占比": f"{'+' if retail_net_inflow_ratio >= 0 else ''}{retail_net_inflow_ratio}%"
                }
                
                formatted_data.append(formatted_item)
            
            return formatted_data

        try:
            logger.info(f"获取历史资金流向数据: stock_code={stock_code}")
            
            # 通过数据源获取数据
            fund_flow_data = data_source.get_historical_fund_flow(stock_code)
            
            if not fund_flow_data:
                return "未找到历史资金流向数据"
            
            # 格式化数据
            formatted_data = _format_fund_flow_data(fund_flow_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            # 获取名称
            index_name = fund_flow_data.get("name", "未知")
            
            return f"## {index_name}历史资金流向数据\n\n{table}\n\n💡 显示最近10个交易日的资金流向数据，按日期倒序排列"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    logger.info("市场板块行情工具已注册")