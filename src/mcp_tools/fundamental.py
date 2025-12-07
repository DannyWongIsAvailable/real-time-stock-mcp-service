"""
基本面数据工具
src/mcp_tools/fundamental.py
提供基本面数据查询功能
"""
import logging
from mcp.server.fastmcp import FastMCP
from ..data_source_interface import FinancialDataInterface
from ..utils.markdown_formatter import format_list_to_markdown_table

logger = logging.getLogger(__name__)


def register_fundamental_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册基本面数据相关工具

    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

    @app.tool()
    def get_business_scope(stock_code: str) -> str:
        """
        获取主营业务范围

        获取指定股票的主营业务范围信息。

        Args:
            stock_code: 股票代码，包含交易所代码，格式如300059.SZ

        Returns:
            主营业务范围文本

        Examples:
            - get_business_scope("688041.SH")
        """
        try:
            logger.info(f"获取主营业务范围: {stock_code}")

            # 从数据源获取原始数据
            raw_data = data_source.get_business_scope(stock_code)

            if not raw_data:
                return f"未找到股票代码 '{stock_code}' 的主营业务范围数据"

            # 检查是否有错误信息
            if "error" in raw_data:
                error_msg = raw_data["error"]
                return f"获取主营业务范围数据失败: {error_msg}"

            # 提取BUSINESS_SCOPE内容
            business_scope = raw_data.get('BUSINESS_SCOPE', 'N/A')
            
            return business_scope

        except Exception as e:
            logger.error(f"获取主营业务范围时出错: {e}")
            return f"获取主营业务范围失败: {str(e)}"

    @app.tool()
    def get_main_business(stock_code: str) -> str:
        """
        获取主营构成分析

        获取指定股票的主营构成分析数据。

        Args:
            stock_code: 股票代码，必须在后面加上交易所代码，如300059.SZ

        Returns:
            主营业务构成数据的Markdown表格

        Examples:
            - get_main_business("300059.SZ")
        """
        try:
            logger.info(f"获取主营业务构成: {stock_code}")

            # 获取最新的报告日期
            raw_report_dates = data_source.get_report_dates(stock_code)
            if not raw_report_dates or (isinstance(raw_report_dates, list) and len(raw_report_dates) == 0):
                return f"未找到股票代码 '{stock_code}' 的报告日期数据"

            # 检查是否有错误信息
            if isinstance(raw_report_dates, list) and len(raw_report_dates) > 0 and "error" in raw_report_dates[0]:
                error_msg = raw_report_dates[0]["error"]
                return f"获取报告日期数据失败: {error_msg}"

            # 只处理第一个数据（最近的报告日期）
            latest_report = raw_report_dates[0]
            report_date = latest_report.get('REPORT_DATE', 'N/A')
            # 只取日期部分，去除时间部分
            if report_date != 'N/A' and ' ' in report_date:
                report_date = report_date.split(' ')[0]

            # 从数据源获取原始数据
            raw_data = data_source.get_main_business(stock_code, report_date)

            if not raw_data:
                return f"未找到股票代码 '{stock_code}' 的主营业务构成数据"

            # 检查是否有错误信息
            if isinstance(raw_data, list) and len(raw_data) > 0 and "error" in raw_data[0]:
                error_msg = raw_data[0]["error"]
                return f"获取主营业务构成数据失败: {error_msg}"

            # 格式化数据
            formatted_data = []
            for item in raw_data:
                # 解析主营业务分类类型
                mainop_type = item.get('MAINOP_TYPE', 'N/A')
                type_mapping = {
                    '1': '按行业分类',
                    '2': '按产品分类',
                    '3': '按地区分类'
                }
                type_desc = type_mapping.get(mainop_type, f'未知分类({mainop_type})')
                
                formatted_item = {
                    '报告日期': item.get('REPORT_DATE', 'N/A')[:10],  # 只取日期部分
                    '分类依据': type_desc,
                    '主营构成': item.get('ITEM_NAME', 'N/A'),
                    '主营业务收入': f"{item.get('MAIN_BUSINESS_INCOME', 'N/A'):,.2f} 元" if item.get('MAIN_BUSINESS_INCOME') is not None else 'N/A',
                    '收入占比': f"{item.get('MBI_RATIO', 0) * 100:.2f}%" if item.get('MBI_RATIO') is not None else 'N/A',
                    '主营业务成本': f"{item.get('MAIN_BUSINESS_COST', 'N/A'):,.2f} 元" if item.get('MAIN_BUSINESS_COST') is not None else 'N/A',
                    '成本占比': f"{item.get('MBC_RATIO', 0) * 100:.2f}%" if item.get('MBC_RATIO') is not None else 'N/A',
                    '主营业务利润': f"{item.get('MAIN_BUSINESS_RPOFIT', 'N/A'):,.2f} 元" if item.get('MAIN_BUSINESS_RPOFIT') is not None else 'N/A',
                    '利润占比': f"{item.get('MBR_RATIO', 0) * 100:.2f}%" if item.get('MBR_RATIO') is not None else 'N/A',
                    '毛利率': f"{item.get('GROSS_RPOFIT_RATIO', 0) * 100:.2f}%" if item.get('GROSS_RPOFIT_RATIO') is not None else 'N/A',
                    '排序': item.get('RANK', 'N/A')
                }
                formatted_data.append(formatted_item)

            table = format_list_to_markdown_table(formatted_data)
            note = f"\n\n💡 显示 {len(formatted_data)} 条主营业务构成数据"
            
            if report_date:
                note += f"，报告期: {report_date}"
                
            return f"## {stock_code} 主营业务构成\n\n{table}{note}"

        except Exception as e:
            logger.error(f"获取主营业务构成时出错: {e}")
            return f"获取主营业务构成失败: {str(e)}"

    @app.tool()
    def get_business_review(stock_code: str) -> str:
        """
        获取经营评述

        获取指定股票的经营评述信息。

        Args:
            stock_code: 股票代码，必须在后面加上交易所代码，格式如300059.SZ

        Returns:
            经营评述文本

        Examples:
            - get_business_review("688041.SH")
        """
        try:
            logger.info(f"获取经营评述: {stock_code}")

            # 从数据源获取原始数据
            raw_data = data_source.get_business_review(stock_code)

            if not raw_data:
                return f"未找到股票代码 '{stock_code}' 的经营评述数据"

            # 检查是否有错误信息
            if "error" in raw_data:
                error_msg = raw_data["error"]
                return f"获取经营评述数据失败: {error_msg}"

            # 提取BUSINESS_REVIEW内容
            business_review = raw_data.get('BUSINESS_REVIEW', 'N/A')

            # 返回经营评述内容，如果没有则返回提示信息
            if business_review and business_review != 'N/A':
                return business_review
            else:
                return f"股票代码 '{stock_code}' 无经营评述数据"

        except Exception as e:
            logger.error(f"获取经营评述时出错: {e}")
            return f"获取经营评述失败: {str(e)}"