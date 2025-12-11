"""
估值数据工具
src/mcp_tools/valuation.py
提供估值数据查询和分析功能
"""
import logging
from mcp.server.fastmcp import FastMCP
from ..data_source_interface import FinancialDataInterface
from ..utils.markdown_formatter import format_list_to_markdown_table

logger = logging.getLogger(__name__)


def register_valuation_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册估值分析工具到MCP应用
    
    Args:
        app: FastMCP应用实例
        data_source: 数据源接口实例
    """
    
    @app.tool()
    def get_institutional_rating(stock_code: str, begin_time: str, end_time: str) -> str:
        """
        获取机构评级数据

        Args:
            stock_code: 股票代码，纯数字，如688041
            begin_time: 开始时间，格式如2025-10-23
            end_time: 结束时间，格式如2025-12-07

        Returns:
            机构评级数据的Markdown表格

        Examples:
            - get_institutional_rating("688041", "2025-01-01", "2025-12-31")
        """
        try:
            logger.info(f"获取机构评级数据: {stock_code}, 时间范围: {begin_time} 到 {end_time}")

            # 获取机构评级数据
            raw_data = data_source.get_institutional_rating(stock_code, begin_time, end_time)
            
            # 检查是否有错误信息
            if raw_data is None:
                return f"未找到股票代码 '{stock_code}' 的机构评级数据"
            
            # 检查是否返回了错误
            if isinstance(raw_data, list) and len(raw_data) > 0 and "error" in raw_data[0]:
                error_msg = raw_data[0]["error"]
                return f"获取机构评级数据失败: {error_msg}"
            
            # 检查是否为空数据
            if not raw_data:
                return f"在 {begin_time} 到 {end_time} 时间段内未找到股票 '{stock_code}' 的机构评级数据"
            
            # 格式化为表格
            table_data = []
            for item in raw_data:
                # 只处理研究员信息
                researchers = item.get("researcher", "N/A")

                # 格式化数值字段，保留两位小数
                predict_this_year_eps = item.get("predictThisYearEps", "N/A")
                if predict_this_year_eps != "N/A" and isinstance(predict_this_year_eps, (int, float, str)) and str(predict_this_year_eps).replace('.', '', 1).isdigit():
                    predict_this_year_eps = f"{float(predict_this_year_eps):.2f}"
                
                predict_this_year_pe = item.get("predictThisYearPe", "N/A")
                if predict_this_year_pe != "N/A" and isinstance(predict_this_year_pe, (int, float, str)) and str(predict_this_year_pe).replace('.', '', 1).isdigit():
                    predict_this_year_pe = f"{float(predict_this_year_pe):.2f}"
                
                predict_next_year_eps = item.get("predictNextYearEps", "N/A")
                if predict_next_year_eps != "N/A" and isinstance(predict_next_year_eps, (int, float, str)) and str(predict_next_year_eps).replace('.', '', 1).isdigit():
                    predict_next_year_eps = f"{float(predict_next_year_eps):.2f}"
                
                predict_next_year_pe = item.get("predictNextYearPe", "N/A")
                if predict_next_year_pe != "N/A" and isinstance(predict_next_year_pe, (int, float, str)) and str(predict_next_year_pe).replace('.', '', 1).isdigit():
                    predict_next_year_pe = f"{float(predict_next_year_pe):.2f}"

                formatted_item = {
                    "发布日期": item.get("publishDate", "N/A")[:10] if item.get("publishDate") else "N/A",
                    "研报标题": item.get("title", "N/A")[:50] + "..." if item.get("title") and len(item.get("title")) > 50 else item.get("title", "N/A"),
                    "评级": item.get("emRatingName", item.get("sRatingName", "N/A")),
                    "机构名称": item.get("orgName", "N/A"),
                    "预期EPS": predict_this_year_eps,
                    "预期PE": predict_this_year_pe,
                    "明年预期EPS": predict_next_year_eps,
                    "明年预期PE": predict_next_year_pe,
                    "研究员": researchers,

                }
                table_data.append(formatted_item)
            
            result = f"**机构评级数据 (共{len(table_data)}条)**\n\n"
            result += format_list_to_markdown_table(table_data)
            
            return result

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"
    
    @app.tool()
    def get_valuation_analysis(stock_code: str, date_type: int = 3) -> str:
        """
        获取指定股票的所有估值分析数据，包括市盈率、市净率、市销率和市现率的当前值和历史分位数。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
            date_type: 时间周期类型
                     1 - 1年
                     2 - 3年
                     3 - 5年
                     4 - 10年

        Returns:
            所有估值分析数据的Markdown表格

        Examples:
            - get_valuation_analysis("300750.SZ", 3)
            - get_valuation_analysis("300750.SZ", 2)
        """
        try:
            logger.info(f"获取估值分析数据: {stock_code}, 时间周期: {date_type}")

            # 获取估值分析数据
            raw_data = data_source.get_valuation_analysis(stock_code, date_type)

            # 检查是否有错误信息
            if raw_data is None:
                return f"未找到股票代码 '{stock_code}' 的估值分析数据"
            
            if isinstance(raw_data, list) and len(raw_data) > 0 and "error" in raw_data[0]:
                error_msg = raw_data[0]["error"]
                return f"获取估值分析数据失败: {error_msg}"
            
            # 交易日期
            trade_date = raw_data[0]["TRADE_DATE"].split(" ")[0] if raw_data and raw_data[0].get("TRADE_DATE") else "N/A"
            # 统计周期
            statistics_cycle = raw_data[0]["STATISTICS_CYCLE"] if raw_data and raw_data[0].get("STATISTICS_CYCLE") else "N/A"

            # 格式化为表格
            table_data = []
            for indicator_data in raw_data:
                formatted_row = {
                    "指标类型": indicator_data.get("INDICATOR_TYPE", "N/A"),
                    "指标值": f"{indicator_data.get('INDICATOR_VALUE', 'N/A'):.4f}" if indicator_data.get('INDICATOR_VALUE') is not None else 'N/A',
                    "30%分位数": f"{indicator_data.get('PERCENTILE_THIRTY', 'N/A'):.4f}" if indicator_data.get('PERCENTILE_THIRTY') is not None else 'N/A',
                    "中位数(50%)": f"{indicator_data.get('PERCENTILE_FIFTY', 'N/A'):.4f}" if indicator_data.get('PERCENTILE_FIFTY') is not None else 'N/A',
                    "70%分位数": f"{indicator_data.get('PERCENTILE_SEVENTY', 'N/A'):.4f}" if indicator_data.get('PERCENTILE_SEVENTY') is not None else 'N/A'
                }
                table_data.append(formatted_row)
            
            result = f"**估值分析数据 **\n\n"
            result += format_list_to_markdown_table(table_data)
            result += f"\n截至 {trade_date}， 统计周期:{statistics_cycle} "
            
            return result

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_growth_comparison(stock_code: str) -> str:
        """
        获取成长性比较数据

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ

        Returns:
            成长性比较数据的Markdown表格

        Examples:
            - get_growth_comparison("300750.SZ")
        """
        try:
            logger.info(f"获取成长性比较数据: {stock_code}")

            # 获取成长性比较数据
            raw_data = data_source.get_growth_comparison(stock_code)

            # 检查是否有错误信息
            if raw_data is None:
                return f"未找到股票代码 '{stock_code}' 的成长性比较数据"
            
            if isinstance(raw_data, list) and len(raw_data) > 0 and "error" in raw_data[0]:
                error_msg = raw_data[0]["error"]
                return f"获取成长性比较数据失败: {error_msg}"
            
            # 检查是否为空数据
            if not raw_data:
                return f"未找到股票 '{stock_code}' 的成长性比较数据"
            
            # 格式化为表格
            table_data = []
            for item in raw_data:
                # 格式化数值字段，保留两位小数
                def format_value(value):
                    if value is None or value == "":
                        return "N/A"
                    try:
                        return f"{float(value):.2f}"
                    except (ValueError, TypeError):
                        return str(value)

                formatted_item = {
                    "证券代码": item.get("CORRE_SECURITY_CODE", "N/A"),
                    "证券名称": item.get("CORRE_SECURITY_NAME", "N/A"),
                    "基本每股收益增长率": format_value(item.get("MGSYTB")),
                    "基本每股收益3年复合增长率": format_value(item.get("MGSY_3Y")),
                    "基本每股收益增长率(TTM)": format_value(item.get("MGSYTTM")),
                    "基本每股收益增长率(第1年)": format_value(item.get("MGSY_1E")),
                    "基本每股收益增长率(第2年)": format_value(item.get("MGSY_2E")),
                    "基本每股收益增长率(第3年)": format_value(item.get("MGSY_3E")),
                    "营业收入增长率": format_value(item.get("YYSRTB")),
                    "营业收入3年复合增长率": format_value(item.get("YYSR_3Y")),
                    "营业收入增长率(TTM)": format_value(item.get("YYSRTTM")),
                    "营业收入增长率(第1年)": format_value(item.get("YYSR_1E")),
                    "营业收入增长率(第2年)": format_value(item.get("YYSR_2E")),
                    "营业收入增长率(第3年)": format_value(item.get("YYSR_3E")),
                    "净利润增长率": format_value(item.get("JLRTB")),
                    "净利润3年复合增长率": format_value(item.get("JLR_3Y")),
                    "净利润增长率(TTM)": format_value(item.get("JLRTTM")),
                    "净利润增长率(第1年)": format_value(item.get("JLR_1E")),
                    "净利润增长率(第2年)": format_value(item.get("JLR_2E")),
                    "净利润增长率(第3年)": format_value(item.get("JLR_3E")),
                    "行业排名": item.get("PAIMING"),
                }
                table_data.append(formatted_item)
            
            result = f"**成长性比较数据 (共{len(table_data)}条记录)**\n\n"
            result += format_list_to_markdown_table(table_data)
            
            # 添加报告日期信息
            if raw_data and raw_data[0].get("REPORT_DATE"):
                report_date = raw_data[0]["REPORT_DATE"].split(" ")[0]
                result += f"\n\n数据截止日期: {report_date}"
            
            return result

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_dupont_analysis_comparison(stock_code: str) -> str:
        """
        获取杜邦分析比较数据

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如600000.SH

        Returns:
            杜邦分析比较数据的Markdown表格

        Examples:
            - get_dupont_analysis_comparison("600000.SH")
        """
        try:
            logger.info(f"获取杜邦分析比较数据: {stock_code}")

            # 获取杜邦分析比较数据
            raw_data = data_source.get_dupont_analysis_comparison(stock_code)

            # 检查是否有错误信息
            if raw_data is None:
                return f"未找到股票代码 '{stock_code}' 的杜邦分析比较数据"
            
            if isinstance(raw_data, list) and len(raw_data) > 0 and "error" in raw_data[0]:
                error_msg = raw_data[0]["error"]
                return f"获取杜邦分析比较数据失败: {error_msg}"
            
            # 检查是否为空数据
            if not raw_data:
                return f"未找到股票 '{stock_code}' 的杜邦分析比较数据"
            
            # 格式化为表格
            table_data = []
            for item in raw_data:
                # 格式化数值字段，保留两位小数
                def format_value(value):
                    if value is None or value == "":
                        return "N/A"
                    try:
                        return f"{float(value):.2f}"
                    except (ValueError, TypeError):
                        return str(value)

                formatted_item = {
                    "证券代码": item.get("CORRE_SECURITY_CODE", "N/A"),
                    "证券名称": item.get("CORRE_SECURITY_NAME", "N/A"),
                    "净资产收益率(3年平均)": format_value(item.get("ROE_AVG")),
                    "净资产收益率(3年前)": format_value(item.get("ROEPJ_L3")),
                    "净资产收益率(2年前)": format_value(item.get("ROEPJ_L2")),
                    "净资产收益率(1年前)": format_value(item.get("ROEPJ_L1")),
                    "销售净利率(3年平均)": format_value(item.get("XSJLL_AVG")),
                    "销售净利率(3年前)": format_value(item.get("XSJLL_L3")),
                    "销售净利率(2年前)": format_value(item.get("XSJLL_L2")),
                    "销售净利率(1年前)": format_value(item.get("XSJLL_L1")),
                    "总资产周转率(3年平均)": format_value(item.get("TOAZZL_AVG")),
                    "总资产周转率(3年前)": format_value(item.get("TOAZZL_L3")),
                    "总资产周转率(2年前)": format_value(item.get("TOAZZL_L2")),
                    "总资产周转率(1年前)": format_value(item.get("TOAZZL_L1")),
                    "权益乘数(3年平均)": format_value(item.get("QYCS_AVG")),
                    "权益乘数(3年前)": format_value(item.get("QYCS_L3")),
                    "权益乘数(2年前)": format_value(item.get("QYCS_L2")),
                    "权益乘数(1年前)": format_value(item.get("QYCS_L1")),
                    "行业排名": item.get("PAIMING", "N/A"),
                }
                table_data.append(formatted_item)
            
            result = f"**杜邦分析比较数据 (共{len(table_data)}条记录)**\n\n"
            result += format_list_to_markdown_table(table_data)
            
            # 添加报告日期信息
            if raw_data and raw_data[0].get("REPORT_DATE"):
                report_date = raw_data[0]["REPORT_DATE"].split(" ")[0]
                result += f"\n\n数据截止日期: {report_date}"
            
            return result

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    @app.tool()
    def get_valuation_comparison(stock_code: str) -> str:
        """
        获取估值比较数据

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如600000.SH

        Returns:
            估值比较数据的Markdown表格

        Examples:
            - get_valuation_comparison("600000.SH")
        """
        try:
            logger.info(f"获取估值比较数据: {stock_code}")

            # 获取估值比较数据
            raw_data = data_source.get_valuation_comparison(stock_code)

            # 检查是否有错误信息
            if raw_data is None:
                return f"未找到股票代码 '{stock_code}' 的估值比较数据"
            
            if isinstance(raw_data, list) and len(raw_data) > 0 and "error" in raw_data[0]:
                error_msg = raw_data[0]["error"]
                return f"获取估值比较数据失败: {error_msg}"
            
            # 检查是否为空数据
            if not raw_data:
                return f"未找到股票 '{stock_code}' 的估值比较数据"
            
            # 格式化为表格
            table_data = []
            for item in raw_data:
                # 格式化数值字段，保留两位小数
                def format_value(value):
                    if value is None or value == "":
                        return "N/A"
                    try:
                        return f"{float(value):.2f}"
                    except (ValueError, TypeError):
                        return str(value)

                formatted_item = {
                    "证券代码": item.get("CORRE_SECURITY_CODE", "N/A"),
                    "证券名称": item.get("CORRE_SECURITY_NAME", "N/A"),
                    "市盈率PE(年度)": format_value(item.get("PE")),
                    "市盈率PE(TTM)": format_value(item.get("PE_TTM")),
                    "市盈率PE(第一年预测)": format_value(item.get("PE_1Y")),
                    "市盈率PE(第二年预测)": format_value(item.get("PE_2Y")),
                    "市盈率PE(第三年预测)": format_value(item.get("PE_3Y")),
                    "市销率PS(年度)": format_value(item.get("PS")),
                    "市销率PS(TTM)": format_value(item.get("PS_TTM")),
                    "市销率PS(第一年预测)": format_value(item.get("PS_1Y")),
                    "市销率PS(第二年预测)": format_value(item.get("PS_2Y")),
                    "市销率PS(第三年预测)": format_value(item.get("PS_3Y")),
                    "市净率PB(年度)": format_value(item.get("PB")),
                    "市净率PB(MRQ)": format_value(item.get("PB_MRQ")),
                    "市现率PCE(年度)": format_value(item.get("PCE")),
                    "市现率PCE(TTM)": format_value(item.get("PCE_TTM")),
                    "市现率PCF(年度)": format_value(item.get("PCF")),
                    "市现率PCF(TTM)": format_value(item.get("PCF_TTM")),
                    "企业倍数EV/EBITDA(年度)": format_value(item.get("QYBS")),
                    "PEG": format_value(item.get("PEG")),
                    "行业排名": item.get("PAIMING", "N/A"),
                }
                table_data.append(formatted_item)
            
            result = f"**估值比较数据 (共{len(table_data)}条记录)**\n\n"
            result += format_list_to_markdown_table(table_data)
            
            # 添加报告日期信息
            if raw_data and raw_data[0].get("REPORT_DATE"):
                report_date = raw_data[0]["REPORT_DATE"].split(" ")[0]
                result += f"\n\n数据截止日期: {report_date}"
            
            return result

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    logger.info("估值分析工具已注册")
