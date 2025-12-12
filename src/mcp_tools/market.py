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
    def get_plate_quotation(plate_type: int = 2, page_size: int = 10) -> str:
        """
        获取东方财富网的涨跌幅前N板块行情数据，包括行业板块、概念板块、地域板块等。

        Args:
            plate_type: 板块类型参数
                - 1: 地域板块  
                - 2: 行业板块 (默认)
                - 3: 概念板块
            page_size: 返回数据条数，默认为10条

        Returns:
            格式化的板块行情数据，以Markdown表格形式展示

        Examples:
            - get_plate_quotation()
            - get_plate_quotation(1)
            - get_plate_quotation(3)
            - get_plate_quotation(2, 20)
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
            
            # 获取原始数据
            raw_data = data_source.get_plate_quotation(plate_type, page_size)
            
            if not raw_data:
                return "未找到板块行情数据"
            
            # 格式化数据
            formatted_data = _format_plate_data(raw_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            # 添加说明
            plate_type_map = {1: "地域板块", 2: "行业板块", 3: "概念板块"}
            plate_name = plate_type_map.get(plate_type, "未知板块")
            note = f"\n\n💡 显示涨跌幅前{page_size}{plate_name}的行情数据"
            
            return f"## {plate_name}涨跌幅前{page_size}行情数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_historical_fund_flow(stock_code: str, limit: int = 10) -> str:
        """
        获取指定股票最近N个交易日的资金流向数据，包括主力资金、散户资金、中单资金等的流入流出情况。

        Args:
            stock_code: 股票代码，要在数字后带上交易所代码，格式如688041.SH
            limit: 返回数据条数，默认为10条

        Returns:
            格式化的历史资金流向数据，以Markdown表格形式展示

        Examples:
            - get_historical_fund_flow("688041.SH")
            - get_historical_fund_flow("688041.SH", 20)
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
            fund_flow_data = data_source.get_historical_fund_flow(stock_code, limit)
            
            if not fund_flow_data:
                return "未找到历史资金流向数据"
            
            # 格式化数据
            formatted_data = _format_fund_flow_data(fund_flow_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            # 获取名称
            index_name = fund_flow_data.get("name", "未知")
            
            return f"## {index_name}历史资金流向数据\n\n{table}\n\n💡 显示最近{limit}个交易日的资金流向数据，按日期倒序排列"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_billboard_data(trade_date: str, page_size: int = 10) -> str:
        """
        获取指定交易日的龙虎榜数据，包括股票基本信息、行情数据、资金流向等。

        Args:
            trade_date: 交易日期，格式为 YYYY-MM-DD。
            page_size: 返回数据条数，默认为10条。

        Returns:
            格式化的龙虎榜数据，以Markdown表格形式展示

        Examples:
            - get_billboard_data("2025-11-28")
            - get_billboard_data("2025-11-28", 20)
        """
        def _format_billboard_data(raw_data: List[Dict]) -> List[Dict]:
            """
            格式化龙虎榜数据

            Args:
                raw_data: 原始龙虎榜数据

            Returns:
                格式化后的龙虎榜数据列表
            """
            formatted_data = []
            
            for item in raw_data:
                # 处理基础信息
                security_code = item.get("SECURITY_CODE", "")
                security_name = item.get("SECURITY_NAME_ABBR", "")
                
                # 处理行情数据
                close_price = item.get("CLOSE_PRICE", 0)
                change_rate = item.get("CHANGE_RATE", 0)
                turnover_rate = item.get("TURNOVERRATE", 0)
                
                # 处理资金数据 (单位转换)
                # 龙虎榜资金数据单位为元，需要转换为万元显示
                billboard_net_amt = item.get("BILLBOARD_NET_AMT", 0)  # 净买额
                billboard_buy_amt = item.get("BILLBOARD_BUY_AMT", 0)  # 买入额
                billboard_sell_amt = item.get("BILLBOARD_SELL_AMT", 0)  # 卖出额
                billboard_deal_amt = item.get("BILLBOARD_DEAL_AMT", 0)  # 成交额
                accum_amount = item.get("ACCUM_AMOUNT", 0)  # 市场总成交额
                
                # 流通市值 (单位转换为亿元)
                free_market_cap = item.get("FREE_MARKET_CAP", 0)  # 流通市值(元)
                
                # 处理占比数据
                deal_net_ratio = item.get("DEAL_NET_RATIO", 0)  # 净买额占总成交比
                deal_amount_ratio = item.get("DEAL_AMOUNT_RATIO", 0)  # 成交额占总成交比
                
                # 解读说明
                explain = item.get("EXPLAIN", "")
                explanation = item.get("EXPLANATION", "")  # 上榜原因
                
                formatted_item = {
                    "证券代码": security_code,
                    "名称": security_name,
                    "收盘价": f"{close_price:.2f}元" if close_price else "N/A",
                    "涨跌幅": f"{'+' if change_rate >= 0 else ''}{change_rate:.2f}%" if change_rate is not None else "N/A",
                    "换手率": f"{turnover_rate:.2f}%" if turnover_rate is not None else "N/A",
                    "流通市值": format_large_number(free_market_cap) if free_market_cap else "N/A",
                    "龙虎榜净买额": format_large_number(billboard_net_amt) + "元" if billboard_net_amt else "N/A",
                    "龙虎榜买入额": format_large_number(billboard_buy_amt) + "元" if billboard_buy_amt else "N/A",
                    "龙虎榜卖出额": format_large_number(billboard_sell_amt) + "元" if billboard_sell_amt else "N/A",
                    "龙虎榜成交额": format_large_number(billboard_deal_amt) + "元" if billboard_deal_amt else "N/A",
                    "市场总成交额": format_large_number(accum_amount) + "元" if accum_amount else "N/A",
                    "净买额占总成交比": f"{'+' if deal_net_ratio >= 0 else ''}{deal_net_ratio:.2f}%" if deal_net_ratio is not None else "N/A",
                    "成交额占总成交比": f"{deal_amount_ratio:.2f}%" if deal_amount_ratio is not None else "N/A",
                    "上榜原因": explanation,
                    "解读": explain
                }
                
                formatted_data.append(formatted_item)
            
            return formatted_data

        try:
            logger.info(f"获取龙虎榜数据: trade_date={trade_date}")
            
            # 获取原始数据
            raw_data = data_source.get_billboard_data(trade_date, page_size)
            
            # 检查是否有错误信息
            if raw_data and "error" in raw_data[0]:
                return f"获取龙虎榜数据失败: {raw_data[0]['error']}"
            
            if not raw_data:
                return "未找到龙虎榜数据"
            
            # 格式化数据
            formatted_data = _format_billboard_data(raw_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            # 添加说明
            note = f"\n\n💡 显示涨幅前{page_size}的龙虎榜股票，交易日期: {trade_date}，共{len(raw_data)}条数据"
            
            return f"## 涨幅前{page_size}的龙虎榜数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_stock_billboard_data(stock_code: str, page_size: int = 10) -> str:
        """
        获取龙虎榜上榜历史数据（历次上榜）


        Args:
            stock_code: 股票代码，数字后带上交易所代码，格式如688041.SH
            page_size: 返回数据条数，默认为10条

        Returns:
            格式化的龙虎榜上榜历史数据，以Markdown表格形式展示

        Examples:
            - get_historical_billboard_data("688041.SH")
            - get_historical_billboard_data("688041.SH", 20)
        """
        def _format_stock_billboard_data(raw_data: List[Dict]) -> List[Dict]:
            """
            格式化龙虎榜上榜历史数据

            Args:
                raw_data: 原始龙虎榜历史数据

            Returns:
                格式化后的龙虎榜历史数据列表
            """
            formatted_data = []
            
            for item in raw_data:
                # 处理交易日期
                trade_date = item.get("TRADE_DATE", "")
                if " " in trade_date:
                    trade_date = trade_date.split(" ")[0]
                
                # 处理价格数据
                close_price = item.get("CLOSE_PRICE", 0)
                change_rate = item.get("CHANGE_RATE", 0)
                
                # 处理后续涨跌幅数据
                d1_change = item.get("D1_CLOSE_ADJCHRATE", 0)
                d2_change = item.get("D2_CLOSE_ADJCHRATE", 0)
                d3_change = item.get("D3_CLOSE_ADJCHRATE", 0)
                d5_change = item.get("D5_CLOSE_ADJCHRATE", 0)
                d10_change = item.get("D10_CLOSE_ADJCHRATE", 0)
                d20_change = item.get("D20_CLOSE_ADJCHRATE", 0)
                d30_change = item.get("D30_CLOSE_ADJCHRATE", 0)
                
                # 处理资金数据
                net_buy_amt = item.get("NET_BUY_AMT", 0)
                net_sell_amt = item.get("NET_SELL_AMT", 0)
                net_operatedept_amt = item.get("NET_OPERATEDEPT_AMT", 0)
                
                # 解读说明
                explain = item.get("EXPLAIN", "")
                
                formatted_item = {
                    "日期": trade_date,
                    "收盘价": f"{close_price:.2f}元" if close_price else "N/A",
                    "涨跌幅": f"{'+' if change_rate >= 0 else ''}{change_rate:.2f}%",
                    "上榜原因": explain,
                    "后1日涨跌幅": f"{'+' if d1_change >= 0 else ''}{d1_change:.2f}%",
                    "后2日涨跌幅": f"{'+' if d2_change >= 0 else ''}{d2_change:.2f}%",
                    "后3日涨跌幅": f"{'+' if d3_change >= 0 else ''}{d3_change:.2f}%",
                    "后5日涨跌幅": f"{'+' if d5_change >= 0 else ''}{d5_change:.2f}%",
                    "后10日涨跌幅": f"{'+' if d10_change >= 0 else ''}{d10_change:.2f}%",
                    "后20日涨跌幅": f"{'+' if d20_change >= 0 else ''}{d20_change:.2f}%",
                    "后30日涨跌幅": f"{'+' if d30_change >= 0 else ''}{d30_change:.2f}%",
                    "营业部买入金额": format_large_number(net_buy_amt) + "元" if net_buy_amt else "N/A",
                    "营业部卖出金额": format_large_number(net_sell_amt) + "元" if net_sell_amt else "N/A",
                    "营业部实际净买额": format_large_number(net_operatedept_amt) + "元" if net_operatedept_amt else "N/A"
                }
                
                formatted_data.append(formatted_item)
            
            return formatted_data

        try:
            logger.info(f"获取龙虎榜历史数据: stock_code={stock_code}")

            # 获取原始数据
            raw_data = data_source.get_stock_billboard_data(stock_code, page_size)
            
            # 检查是否有错误信息
            if raw_data and "error" in raw_data[0]:
                return f"获取龙虎榜上榜历史记录失败: {raw_data[0]['error']}"
            
            if not raw_data:
                return "未找到龙虎榜上榜历史记录"
            
            # 格式化数据
            formatted_data = _format_stock_billboard_data(raw_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            # 获取股票名称
            stock_name = ""
            if raw_data and isinstance(raw_data, list) and len(raw_data) > 0:
                stock_name = raw_data[0].get("SECURITY_NAME_ABBR", "")
            
            # 添加说明
            note = f"\n\n💡 显示{stock_name}({stock_code})历史龙虎榜上榜记录，共{len(formatted_data)}条记录"
            
            return f"## {stock_name}({stock_code})历史龙虎榜上榜记录\n\n{table}{note}"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_market_performance(secucode: str) -> str:
        """
        获取股票市场表现数据，包括与大盘和行业板块的涨跌对比

        Args:
            secucode: 股票代码，包含交易所代码，如 300750.SZ

        Returns:
            格式化的市场表现数据，以Markdown表格形式展示

        Examples:
            - get_market_performance("300750.SZ")
        """
        def _format_market_performance_data(raw_data: List[Dict]) -> List[Dict]:
            """
            格式化市场表现数据

            Args:
                raw_data: 原始市场表现数据

            Returns:
                格式化后的市场表现数据列表
            """
            # 创建一个字典来存储不同时间段的数据
            time_type_mapping = {
                1: "最近1个月累计涨跌幅",
                2: "最近3个月累计涨跌幅",
                3: "最近6个月累计涨跌幅",
                4: "今年以来累计涨跌幅"
            }
            
            # 初始化结果数据结构
            result_data = {}
            
            # 处理每条记录
            for item in raw_data:
                time_type = item.get("TIME_TYPE")
                time_period = time_type_mapping.get(time_type, f"时期{time_type}")
                
                # 添加股票数据
                secucode = item.get("SECUCODE", "")
                security_name = item.get("SECURITY_NAME_ABBR", "")
                stock_key = f"{secucode}_{security_name}"
                if stock_key not in result_data:
                    result_data[stock_key] = {
                        "代码": secucode,
                        "名称": security_name
                    }
                result_data[stock_key][time_period] = f"{item.get('CHANGERATE', 0):.2f}%"
                
                # 添加沪深300指数数据
                hs300_secucode = item.get("HS300_SECUCODE", "")
                hs300_name = item.get("HS300_NAME", "沪深300")
                hs300_key = f"{hs300_secucode}_{hs300_name}"
                if hs300_key not in result_data:
                    result_data[hs300_key] = {
                        "代码": hs300_secucode,
                        "名称": hs300_name
                    }
                result_data[hs300_key][time_period] = f"{item.get('HS300_CHANGERATE', 0):.2f}%"
                
                # 添加所属板块数据
                board_code = item.get("BOARD_CODE", "")
                board_name = item.get("BOARD_NAME", "")
                board_key = f"{board_code}_{board_name}"
                if board_key not in result_data:
                    result_data[board_key] = {
                        "代码": board_code,
                        "名称": board_name
                    }
                result_data[board_key][time_period] = f"{item.get('BOARD_CHANGERATE', 0):.2f}%"
            
            # 转换为列表格式并确保所有列都有值
            formatted_list = []
            for key, item in result_data.items():
                formatted_item = {
                    "代码": item.get("代码", ""),
                    "名称": item.get("名称", ""),
                    "最近1个月累计涨跌幅": item.get("最近1个月累计涨跌幅", "N/A"),
                    "最近3个月累计涨跌幅": item.get("最近3个月累计涨跌幅", "N/A"),
                    "最近6个月累计涨跌幅": item.get("最近6个月累计涨跌幅", "N/A"),
                    "今年以来累计涨跌幅": item.get("今年以来累计涨跌幅", "N/A")
                }
                formatted_list.append(formatted_item)
                
            return formatted_list

        try:
            logger.info(f"获取市场表现数据: secucode={secucode}")
            
            # 获取原始数据
            raw_data = data_source.get_market_performance(secucode)
            
            if not raw_data:
                return "未找到市场表现数据"
            
            # 格式化数据
            formatted_data = _format_market_performance_data(raw_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            # 获取股票名称
            stock_name = ""
            if raw_data and isinstance(raw_data, list) and len(raw_data) > 0:
                stock_name = raw_data[0].get("SECURITY_NAME_ABBR", "")
            
            return f"## {stock_name}({secucode})市场表现数据\n\n{table}\n\n💡 显示{stock_name}与沪深300指数及所属行业板块的涨跌对比"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_plate_fund_flow(plate_type: int = 2, page_size: int = 10) -> str:
        """
        获取板块资金流今日排行，包括行业板块、概念板块、地域板块等的资金流入流出情况。

        Args:
            plate_type: 板块类型参数
                - 1: 地域板块  
                - 2: 行业板块 (默认)
                - 3: 概念板块
            page_size: 返回数据条数，默认为10条

        Returns:
            格式化的板块资金流数据，以Markdown表格形式展示

        Examples:
            - get_plate_fund_flow()
            - get_plate_fund_flow(1)
            - get_plate_fund_flow(3)
            - get_plate_fund_flow(2, 20)
        """
        def _format_plate_fund_flow_data(raw_data: List[Dict]) -> List[Dict]:
            """
            格式化板块资金流数据

            Args:
                raw_data: 原始板块资金流数据

            Returns:
                格式化后的板块资金流数据列表
            """
            formatted_data = []

            for item in raw_data:
                # 基本信息
                plate_code = item.get("f12", "")
                plate_name = item.get("f14", "")
                
                # 价格信息
                current_price = item.get("f2", 0)  if item.get("f2") else 0
                change_percent = item.get("f3", 0) if item.get("f3") else 0
                
                # 资金流信息
                main_net_inflow = item.get("f62", 0)  # 主力净流入
                super_large_net_inflow = item.get("f66", 0)  # 超大单净流入
                large_net_inflow = item.get("f72", 0)  # 大单净流入
                medium_net_inflow = item.get("f78", 0)  # 中单净流入
                small_net_inflow = item.get("f84", 0)  # 小单净流入
                
                # 资金流占比
                main_net_inflow_ratio = item.get("f184", 0) if item.get("f184") else 0  # 主力净流入占比
                super_large_ratio = item.get("f69", 0) if item.get("f69") else 0  # 超大单净流入占比
                large_ratio = item.get("f75", 0) if item.get("f75") else 0  # 大单净流入占比
                medium_ratio = item.get("f81", 0) if item.get("f81") else 0  # 中单净流入占比
                small_ratio = item.get("f87", 0) if item.get("f87") else 0  # 小单净流入占比
                
                # 领涨股信息
                leading_stock_name = item.get("f204", "")
                leading_stock_code = item.get("f205", "")
                
                formatted_item = {
                    "板块代码": plate_code,
                    "板块名称": plate_name,
                    "当前价格": f"{current_price:.2f}",
                    "涨跌幅": f"{'+' if change_percent >= 0 else ''}{change_percent:.2f}%",
                    "主力净流入": format_large_number(main_net_inflow),
                    "主力净流入占比": f"{'+' if main_net_inflow_ratio >= 0 else ''}{main_net_inflow_ratio:.2f}%",
                    "超大单净流入": format_large_number(super_large_net_inflow),
                    "超大单净流入占比": f"{'+' if super_large_ratio >= 0 else ''}{super_large_ratio:.2f}%",
                    "大单净流入": format_large_number(large_net_inflow),
                    "大单净流入占比": f"{'+' if large_ratio >= 0 else ''}{large_ratio:.2f}%",
                    "中单净流入": format_large_number(medium_net_inflow),
                    "中单净流入占比": f"{'+' if medium_ratio >= 0 else ''}{medium_ratio:.2f}%",
                    "小单净流入": format_large_number(small_net_inflow),
                    "小单净流入占比": f"{'+' if small_ratio >= 0 else ''}{small_ratio:.2f}%",
                    "领涨股": f"{leading_stock_name}({leading_stock_code})"
                }

                formatted_data.append(formatted_item)

            return formatted_data

        try:
            logger.info(f"获取板块资金流数据: 板块类型={plate_type}")
            
            # 获取原始数据
            raw_data = data_source.get_plate_fund_flow(plate_type, page_size)
            
            if not raw_data:
                return "未找到板块资金流数据"
            
            # 格式化数据
            formatted_data = _format_plate_fund_flow_data(raw_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            # 添加说明
            plate_type_map = {1: "地域板块", 2: "行业板块", 3: "概念板块"}
            plate_name = plate_type_map.get(plate_type, "未知板块")
            note = f"\n\n💡 显示{plate_name}资金流数据，按主力净流入排序，共{len(formatted_data)}条数据"
            
            return f"## {plate_name}资金流数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_current_plate_changes(page_size: int = 10) -> str:
        """
        获取当日板块异动数据，包括各板块的涨跌幅、主力资金流向以及板块内异动个股等信息（异动总次数降序）。

        Args:
            page_size: 返回数据条数，默认为10条

        Returns:
            格式化的当日板块异动数据，以Markdown表格形式展示

        Examples:
            - get_current_plate_changes()
            - get_current_plate_changes(30)
        """
        # 异动类型ID映射表
        abnormal_type_map = {
            "1": "顶级买单",
            "2": "顶级卖单",
            "4": "封涨停板",
            "8": "封跌停板",
            "16": "打开涨停板",
            "32": "打开跌停板",
            "64": "有大买盘",
            "128": "有大卖盘",
            "256": "机构买单",
            "512": "机构卖单",
            "8193": "大笔买入",
            "8194": "大笔卖出",
            "8195": "拖拉机买",
            "8196": "拖拉机卖",
            "8201": "火箭发射",
            "8202": "快速反弹",
            "8203": "高台跳水",
            "8204": "加速下跌",
            "8205": "买入撤单",
            "8206": "卖出撤单",
            "8207": "竞价上涨",
            "8208": "竞价下跌",
            "8209": "高开5日线",
            "8210": "低开5日线",
            "8213": "60日新高",
            "8214": "60日新低",
            "8215": "60日大幅上涨",
            "8216": "60日大幅下跌",
            "8217": "未知类型",
            "8218": "未知类型",
            "8219": "未知类型",
            "8220": "未知类型",
            "8221": "未知类型",
            "8222": "未知类型"
        }

        def _format_abnormal_distribution(ydl_list: List[Dict]) -> List[str]:
            """
            格式化异动类型分布数组

            Args:
                ydl_list: 异动类型分布数组

            Returns:
                格式化后的异动类型分布列表
            """
            result = []
            # 按出现次数降序排列
            sorted_ydl = sorted(ydl_list, key=lambda x: x.get("ct", 0), reverse=True)
            for item in sorted_ydl:
                t = str(item.get("t", ""))
                ct = item.get("ct", 0)
                type_name = abnormal_type_map.get(t, f"未知类型({t})")
                result.append(f"{type_name}({ct})")
            return result

        def _format_plate_changes_data(raw_data: List[Dict]) -> List[Dict]:
            """
            格式化板块异动数据

            Args:
                raw_data: 原始板块异动数据

            Returns:
                格式化后的板块异动数据列表
            """
            formatted_data = []

            for item in raw_data:
                # 基本信息
                plate_code = item.get("c", "")          # 板块代码
                plate_name = item.get("n", "")          # 板块名称
                change_percent = item.get("u", 0)       # 板块涨跌幅
                main_net_inflow = item.get("zjl", 0) * 1000   # 主力净流入金额（元）
                stock_count = item.get("ct", 0)         # 板块内股票总数
                
                # 板块内异动最多股票信息
                most_abnormal_stock = item.get("ms", {})
                stock_name = most_abnormal_stock.get("n", "")
                t = str(most_abnormal_stock.get("t", ""))
                type_name = abnormal_type_map.get(t, f"未知类型({t})")
                most_abnormal_stock_info = f"{stock_name}({type_name})" if stock_name and type_name else ""
                
                # 异动类型分布
                abnormal_dist = item.get("ydl", [])
                abnormal_dist_formatted = _format_abnormal_distribution(abnormal_dist)

                formatted_item = {
                    "板块代码": plate_code,
                    "板块名称": plate_name,
                    "涨跌幅": f"{'+' if float(change_percent) >= 0 else ''}{change_percent}%",
                    "主力净流入": f"{format_large_number(main_net_inflow)} 元" ,
                    "板块异动总次数": stock_count,
                    "异动异动最频繁个股": most_abnormal_stock_info,
                    "板块具体异动类型列表及出现次数": abnormal_dist_formatted
                }

                formatted_data.append(formatted_item)

            return formatted_data

        try:
            logger.info(f"获取当日板块异动数据")
            
            # 获取原始数据
            raw_data = data_source.get_current_plate_changes(page_size)
            
            if not raw_data:
                return "未找到当日板块异动数据"
            
            # 格式化数据
            formatted_data = _format_plate_changes_data(raw_data)
            
            # 转换为Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            
            return f"## 当日板块异动数据\n\n{table}\n\n💡 显示最近的{len(formatted_data)}个板块异动情况"

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    logger.info("市场板块行情工具已注册")