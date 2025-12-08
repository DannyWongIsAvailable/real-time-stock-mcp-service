"""
财务分析相关工具
src/mcp_tools/financial_analysis.py
提供财务分析功能
"""
import logging
from mcp.server.fastmcp import FastMCP
from ..data_source_interface import FinancialDataInterface
from ..utils.markdown_formatter import format_list_to_markdown_table

logger = logging.getLogger(__name__)


def register_financial_analysis_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册财务分析相关工具

    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

    def _format_currency_value(value):
        """将货币数值格式化为亿或万元单位"""
        if value is None:
            return None
        
        try:
            float_value = float(value)
            if abs(float_value) >= 100000000:  # 大于等于1亿
                return f"{float_value/100000000:.2f}亿"
            elif abs(float_value) >= 10000:  # 大于等于1万
                return f"{float_value/10000:.2f}万"
            else:
                return f"{float_value:.2f}"
        except (ValueError, TypeError):
            return value

    @app.tool()
    def get_financial_summary(stock_code: str, date_type_code: str = "004") -> str:
        """
        获取业绩概况数据

        获取指定股票的业绩概况数据，包括历史各期的营业收入、净利润等财务指标。

        Args:
            stock_code: 股票代码，包含交易所代码，格式如688041.SH
            date_type_code: 报告类型代码
                          "001" - 一季度报告
                          "002" - 半年度报告
                          "003" - 三季度报告
                          "004" - 年度报告

        Returns:
            业绩概况数据的Markdown表格

        Examples:
            - get_financial_summary("688041.SH")
            - get_financial_summary("300750.SZ", "003")
        """
        try:
            logger.info(f"获取股票 {stock_code} 的业绩概况数据")

            # 从数据源获取业绩概况数据
            revenue_data = data_source.get_financial_summary(stock_code, date_type_code)

            if not revenue_data:
                return f"未能获取到股票 {stock_code} 的业绩概况数据"

            # 检查是否返回错误信息
            if isinstance(revenue_data, list) and len(revenue_data) > 0 and "error" in revenue_data[0]:
                return f"获取业绩概况数据失败: {revenue_data[0]['error']}"

            # 格式化数据
            formatted_data = []
            for item in revenue_data:
                # 处理数值格式化
                parent_net_profit = item.get('PARENTNETPROFIT')
                if parent_net_profit is not None:
                    parent_net_profit = f"{_format_currency_value(parent_net_profit)}元"
                
                total_operate_reve = item.get('TOTALOPERATEREVE')
                if total_operate_reve is not None:
                    total_operate_reve = f"{_format_currency_value(total_operate_reve)}元"
                
                kcfjcxsyjlr = item.get('KCFJCXSYJLR')
                if kcfjcxsyjlr is not None:
                    kcfjcxsyjlr = f"{_format_currency_value(kcfjcxsyjlr)}元"
                
                parent_net_profit_ratio = item.get('PARENTNETPROFIT_RATIO')
                if parent_net_profit_ratio is not None:
                    parent_net_profit_ratio = f"{float(parent_net_profit_ratio):.2f}%"
                
                total_operate_reve_ratio = item.get('TOTALOPERATEREVE_RATIO')
                if total_operate_reve_ratio is not None:
                    total_operate_reve_ratio = f"{float(total_operate_reve_ratio):.2f}%"
                
                kcfjcxsyjlr_ratio = item.get('KCFJCXSYJLR_RATIO')
                if kcfjcxsyjlr_ratio is not None:
                    kcfjcxsyjlr_ratio = f"{float(kcfjcxsyjlr_ratio):.2f}%"

                formatted_item = {
                    '报告期': item.get('DATE_TYPE', ''),
                    '报告类型': item.get('TYPE', ''),
                    '营业收入': total_operate_reve,
                    '营业收入同比增长': total_operate_reve_ratio,
                    '归母净利润': parent_net_profit,
                    '归母净利润同比增长率': parent_net_profit_ratio,
                    '扣非净利润': kcfjcxsyjlr,
                    '扣非净利润同比增长': kcfjcxsyjlr_ratio,
                }
                formatted_data.append(formatted_item)

            # 生成Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            note = f"\n\n💡 显示 {len(formatted_data)} 条业绩概况数据"
            return f"## {stock_code} 业绩概况数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"获取业绩概况数据时出错: {e}")
            return f"获取业绩概况数据失败: {str(e)}"

    @app.tool()
    def get_holder_number(stock_code: str) -> str:
        """
        获取股东户数数据

        获取指定股票的股东户数数据，包括历史各期的股东人数及对应的收盘价。

        Args:
            stock_code: 股票代码，包含交易所代码，格式如688041.SH

        Returns:
            股东户数数据的Markdown表格

        Examples:
            - get_holder_number("688041.SH")
        """
        try:
            logger.info(f"获取股票 {stock_code} 的股东户数数据")

            # 从数据源获取股东户数数据
            holder_data = data_source.get_holder_number(stock_code)

            if not holder_data:
                return f"未能获取到股票 {stock_code} 的股东户数数据"

            # 检查是否返回错误信息
            if isinstance(holder_data, list) and len(holder_data) > 0 and "error" in holder_data[0]:
                return f"获取股东户数数据失败: {holder_data[0]['error']}"

            # 格式化数据
            formatted_data = []
            for item in holder_data:
                # 处理数值格式化
                holder_num = item.get('HOLDER_NUM')
                if holder_num is not None:
                    holder_num = f"{holder_num:,}户"
                
                close_price = item.get('CLOSE_PRICE')
                if close_price is not None:
                    close_price = f"{close_price:.2f}元"

                formatted_item = {
                    '股东户数': holder_num,
                    '股价': close_price,
                    '报告期': item.get('REPORT', ''),
                    '截止日期': item.get('END_DATE', '')[:10] if item.get('END_DATE') else '',
                }
                formatted_data.append(formatted_item)

            # 生成Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            note = f"\n\n💡 显示 {len(formatted_data)} 条股东户数数据"
            return f"## {stock_code} 股东户数数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"获取股东户数数据时出错: {e}")
            return f"获取股东户数数据失败: {str(e)}"

    @app.tool()
    def get_industry_profit_comparison(stock_code: str) -> str:
        """
        获取同行业公司盈利对比数据

        获取指定股票的同行业公司盈利对比数据，包括同行业公司的基本财务和盈利指标。

        Args:
            stock_code: 股票代码，必须在在数字后添加交易所代码，如688041.SH

        Returns:
            行业公司盈利数据的Markdown表格

        Examples:
            - get_industry_profit_comparison("688041.SH")
        """
        try:
            # 从数据源获取同行业公司盈利对比数据
            industry_data = data_source.get_industry_profit_comparison(stock_code)

            if not industry_data:
                return f"未能获取到股票 {stock_code} 的同行业公司盈利数据"

            # 检查是否返回错误信息
            if isinstance(industry_data, list) and len(industry_data) > 0 and "error" in industry_data[0]:
                return f"获取同行业公司盈利数据失败: {industry_data[0]['error']}"

            # 格式化数据
            formatted_data = []
            for item in industry_data:
                # 处理数值格式化
                total_market_cap = item.get('TOTAL_MARKET_CAP')
                if total_market_cap is not None:
                    total_market_cap = f"{_format_currency_value(total_market_cap)}元"
                
                pb = item.get('PB')
                if pb is not None:
                    pb = f"{pb:.2f}"
                    
                roe = item.get('ROE')
                if roe is not None:
                    roe = f"{roe:.2f}%"
                
                total_operate_reve = item.get('TOTALOPERATEREVE')
                if total_operate_reve is not None:
                    total_operate_reve = f"{_format_currency_value(total_operate_reve)}元"
                
                parent_net_profit = item.get('PARENTNETPROFIT')
                if parent_net_profit is not None:
                    parent_net_profit = f"{_format_currency_value(parent_net_profit)}元"
                
                # 上一年同期营业收入
                total_operate_reve_l1y = item.get('TOTALOPERATEREVE_L1Y')
                if total_operate_reve_l1y is not None:
                    total_operate_reve_l1y = f"{_format_currency_value(total_operate_reve_l1y)}元"
                
                # 上两年同期营业收入
                total_operate_reve_l2y = item.get('TOTALOPERATEREVE_L2Y')
                if total_operate_reve_l2y is not None:
                    total_operate_reve_l2y = f"{_format_currency_value(total_operate_reve_l2y)}元"
                
                # 上一年同期归母净利润
                parent_net_profit_l1y = item.get('PARENTNETPROFIT_L1Y')
                if parent_net_profit_l1y is not None:
                    parent_net_profit_l1y = f"{_format_currency_value(parent_net_profit_l1y)}元"
                
                # 上两年同期归母净利润
                parent_net_profit_l2y = item.get('PARENTNETPROFIT_L2Y')
                if parent_net_profit_l2y is not None:
                    parent_net_profit_l2y = f"{_format_currency_value(parent_net_profit_l2y)}元"
                
                # 行业平均市净率
                avg_industry_pb = item.get('AVG_INDUSTRY_PB')
                if avg_industry_pb is not None:
                    avg_industry_pb = f"{avg_industry_pb:.2f}"
                
                # 行业平均净资产收益率
                avg_industry_roe = item.get('AVG_INDUSTRY_ROE')
                if avg_industry_roe is not None:
                    avg_industry_roe = f"{avg_industry_roe:.2f}%"

                formatted_item = {
                    '证券代码': item.get('SECURITY_CODE', ''),
                    '证券简称': item.get('SECURITY_NAME_ABBR', ''),
                    '关联代码': item.get('CORRE_SECURITY_CODE', ''),
                    '关联名称': item.get('CORRE_SECURITY_NAME', ''),
                    '行业': item.get('INDUSTRY', ''),
                    '总市值': total_market_cap,
                    '总市值排名': item.get('TOTAL_MARKET_CAP_RANK', ''),
                    '市净率': pb,
                    '市净率排名': item.get('PB_RANK', ''),
                    '行业平均市净率': avg_industry_pb,
                    '净资产收益率': roe,
                    '净资产收益率排名': item.get('ROE_RANK', ''),
                    '行业平均净资产收益率': avg_industry_roe,
                    '营业收入': total_operate_reve,
                    '上年同期营业收入': total_operate_reve_l1y,
                    '上上年营业收入': total_operate_reve_l2y,
                    '营收排名': item.get('TOTALOPERATEREVE_RANK', ''),
                    '归母净利润': parent_net_profit,
                    '上年同期归母净利润': parent_net_profit_l1y,
                    '上上年归母净利润': parent_net_profit_l2y,
                    '是否本股': '是' if item.get('IS_SELF', 0) == 1 else '否',
                    '报告期': item.get('REPORT_DATE', '')[:10] if item.get('REPORT_DATE') else '',
                    '报告类型': item.get('REPORT_TYPE', ''),
                }
                formatted_data.append(formatted_item)

            # 生成Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            note = f"\n\n💡 显示 {len(formatted_data)} 条同行业公司盈利数据"
            return f"## {stock_code} 同行业公司盈利对比数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"获取同行业公司盈利对比数据时出错: {e}")
            return f"获取同行业公司盈利对比数据失败: {str(e)}"

    logger.info("财务分析工具已注册")