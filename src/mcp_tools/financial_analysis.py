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
    def get_financial_summary(stock_code: str) -> str:
        """
        获取业绩概况数据

        获取指定股票的业绩概况数据，包括历史各期的营业收入、净利润等财务指标。

        Args:
            stock_code: 股票代码，包含交易所代码，格式如688041.SH

        Returns:
            业绩概况数据的Markdown表格

        Examples:
            - get_financial_summary("688041.SH")
            - get_financial_summary("300750.SZ")
        """
        try:
            logger.info(f"获取股票 {stock_code} 的业绩概况数据")

            # 从数据源获取业绩概况数据
            revenue_data = data_source.get_financial_summary(stock_code)

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
                    '报告期': item.get('TYPE', ''),
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