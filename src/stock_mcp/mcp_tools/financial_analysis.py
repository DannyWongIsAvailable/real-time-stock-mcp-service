"""
财务分析相关工具
src/mcp_tools/financial_analysis.py
提供财务分析功能
"""
import logging
from mcp.server.fastmcp import FastMCP
from stock_mcp.data_source_interface import FinancialDataInterface
from stock_mcp.utils.markdown_formatter import format_list_to_markdown_table, format_markdown_report

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
        获取指定股票的业绩概况数据，包括历史各期的营业收入、净利润等财务指标。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH
            date_type_code: 报告类型代码
                          "001" - 一季度报告
                          "002" - 半年度报告
                          "003" - 三季度报告
                          "004" - 年度报告

        Returns:
            业绩概况数据的Markdown表格

        Examples:
            - get_financial_summary("688041.SH")
            - get_financial_summary("688041.SH", "003")
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
            return format_markdown_report(
                f"{stock_code} 业绩概况数据",
                table_data=formatted_data,
                footnote=f"💡 显示 {len(formatted_data)} 条业绩概况数据",
            )

        except Exception as e:
            logger.error(f"获取业绩概况数据时出错: {e}")
            return f"获取业绩概况数据失败: {str(e)}"

    @app.tool()
    def get_holder_number(stock_code: str) -> str:
        """
        获取指定股票的股东户数数据，包括历史各期的股东人数及对应的收盘价。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH

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
            return format_markdown_report(
                f"{stock_code} 股东户数数据",
                table_data=formatted_data,
                footnote=f"💡 显示 {len(formatted_data)} 条股东户数数据",
            )

        except Exception as e:
            logger.error(f"获取股东户数数据时出错: {e}")
            return f"获取股东户数数据失败: {str(e)}"

    @app.tool()
    def get_industry_profit_comparison(stock_code: str) -> str:
        """
        获取指定股票的同行业公司盈利对比数据，包括同行业公司的基本财务和盈利指标。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH

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

            return format_markdown_report(
                f"{stock_code} 同行业公司盈利对比数据",
                table_data=formatted_data,
                footnote=f"💡 显示 {len(formatted_data)} 条同行业公司盈利数据",
            )

        except Exception as e:
            logger.error(f"获取同行业公司盈利对比数据时出错: {e}")
            return f"获取同行业公司盈利对比数据失败: {str(e)}"

    @app.tool()
    def get_financial_ratios(stock_code: str) -> str:
        """
        获取指定股票的财务比率数据，包括盈利能力、偿债能力、运营能力等关键财务指标。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ

        Returns:
            财务比率数据的Markdown表格

        Examples:
            - get_financial_ratios("300750.SZ")
        """
        try:
            logger.info(f"获取股票 {stock_code} 的财务比率数据")

            # 从数据源获取财务比率数据
            ratios_data = data_source.get_financial_ratios(stock_code)

            if not ratios_data:
                return f"未能获取到股票 {stock_code} 的财务比率数据"

            # 检查是否返回错误信息
            if isinstance(ratios_data, list) and len(ratios_data) > 0 and "error" in ratios_data[0]:
                return f"获取财务比率数据失败: {ratios_data[0]['error']}"

            # 格式化数据
            formatted_data = []
            for item in ratios_data:
                # 盈利能力指标
                weight_roe = item.get('WEIGHT_ROE')
                if weight_roe is not None:
                    weight_roe = f"{weight_roe:.2f}%"
                
                netprofit_yoy_ratio = item.get('NETPROFIT_YOY_RATIO')
                if netprofit_yoy_ratio is not None:
                    netprofit_yoy_ratio = f"{netprofit_yoy_ratio:.2f}%"
                
                core_rprofit_ratio = item.get('CORE_RPOFIT_RATIO')
                if core_rprofit_ratio is not None:
                    core_rprofit_ratio = f"{core_rprofit_ratio:.2f}%"
                
                gross_rprofit_ratio = item.get('GROSS_RPOFIT_RATIO')
                if gross_rprofit_ratio is not None:
                    gross_rprofit_ratio = f"{gross_rprofit_ratio:.2f}%"

                sale_cash_ratio = item.get('SALE_CASH_RATIO')
                if sale_cash_ratio is not None:
                    sale_cash_ratio = f"{sale_cash_ratio:.2f}%"

                sale_npr = item.get('SALE_NPR')
                if sale_npr is not None:
                    sale_npr = f"{sale_npr:.2f}%"

                # 偿债能力指标
                debt_asset_ratio = item.get('DEBT_ASSET_RATIO')
                if debt_asset_ratio is not None:
                    debt_asset_ratio = f"{debt_asset_ratio:.2f}%"
                
                current_ratio = item.get('CURRENT_RATIO')
                if current_ratio is not None:
                    current_ratio = f"{current_ratio:.2f}"

                # 运营能力指标
                total_assets_tr = item.get('TOTAL_ASSETS_TR')
                if total_assets_tr is not None:
                    total_assets_tr = f"{total_assets_tr:.2f}"
                
                accounts_rece_tr = item.get('ACCOUNTS_RECE_TR')
                if accounts_rece_tr is not None:
                    accounts_rece_tr = f"{accounts_rece_tr:.2f}"
                
                inventory_tr = item.get('INVENTORY_TR')
                if inventory_tr is not None:
                    inventory_tr = f"{inventory_tr:.2f}"
                
                current_total_assets_tr = item.get('CURRENT_TOTAL_ASSETS_TR')
                if current_total_assets_tr is not None:
                    current_total_assets_tr = f"{current_total_assets_tr:.2f}"

                # 成长能力指标
                total_operate_income_ratio = item.get('TOTAL_OPERATE_INCOME_RATIO')
                if total_operate_income_ratio is not None:
                    total_operate_income_ratio = f"{total_operate_income_ratio:.2f}%"
                
                total_assets_ratio = item.get('TOTAL_ASSETS_RATIO')
                if total_assets_ratio is not None:
                    total_assets_ratio = f"{total_assets_ratio:.2f}%"

                # 现金流指标
                netcash_operate = item.get('NETCASH_OPERATE')
                if netcash_operate is not None:
                    netcash_operate = f"{_format_currency_value(netcash_operate)}元"
                
                netcash_invest = item.get('NETCASH_INVEST')
                if netcash_invest is not None:
                    netcash_invest = f"{_format_currency_value(netcash_invest)}元"
                
                netcash_finance = item.get('NETCASH_FINANCE')
                if netcash_finance is not None:
                    netcash_finance = f"{_format_currency_value(netcash_finance)}元"

                # 核心利润和总利润
                core_rprofit = item.get('CORE_RPOFIT')
                if core_rprofit is not None:
                    core_rprofit = f"{_format_currency_value(core_rprofit)}元"
                
                total_profit = item.get('TOTAL_PROFIT')
                if total_profit is not None:
                    total_profit = f"{_format_currency_value(total_profit)}元"

                # 行业排名指标
                weight_roe_rank = item.get('WEIGHT_ROE_RANK')
                if weight_roe_rank is not None:
                    weight_roe_rank = f"前{weight_roe_rank*100:.0f}%"
                
                netprofit_yoy_ratio_rank = item.get('NETPROFIT_YOY_RATIO_RANK')
                if netprofit_yoy_ratio_rank is not None:
                    netprofit_yoy_ratio_rank = f"前{netprofit_yoy_ratio_rank*100:.0f}%"
                
                total_assets_tr_rank = item.get('TOTAL_ASSETS_TR_RANK')
                if total_assets_tr_rank is not None:
                    total_assets_tr_rank = f"前{total_assets_tr_rank*100:.0f}%"
                
                sale_cash_ratio_rank = item.get('SALE_CASH_RATIO_RANK')
                if sale_cash_ratio_rank is not None:
                    sale_cash_ratio_rank = f"前{sale_cash_ratio_rank*100:.0f}%"
                
                debt_asset_ratio_rank = item.get('DEBT_ASSET_RATIO_RANK')
                if debt_asset_ratio_rank is not None:
                    debt_asset_ratio_rank = f"前{debt_asset_ratio_rank*100:.0f}%"

                formatted_item = {
                    '报告期': item.get('DATE_TYPE', ''),
                    '财报日期': item.get('REPORT_DATE', '')[:10] if item.get('REPORT_DATE') else '',
                    '加权ROE': weight_roe,
                    'ROE排名': weight_roe_rank,
                    '净利润增速': netprofit_yoy_ratio,
                    '净利润增速排名': netprofit_yoy_ratio_rank,
                    '毛利率': gross_rprofit_ratio,
                    '净利率': sale_npr,
                    '核心利润率': core_rprofit_ratio,
                    '核心利润': core_rprofit,
                    '利润总额': total_profit,
                    '资产负债率': debt_asset_ratio,
                    '资产负债率排名': debt_asset_ratio_rank,
                    '流动比率': current_ratio,
                    '总资产周转率': total_assets_tr,
                    '总资产周转率排名': total_assets_tr_rank,
                    '销售现金比率': sale_cash_ratio,
                    '销售现金比率排名': sale_cash_ratio_rank,
                    '应收账款周转率': accounts_rece_tr,
                    '存货周转率': inventory_tr,
                    '流动资产周转率': current_total_assets_tr,
                    '营收增速': total_operate_income_ratio,
                    '总资产增速': total_assets_ratio,
                    '经营现金流': netcash_operate,
                    '投资现金流': netcash_invest,
                    '融资现金流': netcash_finance,
                }
                formatted_data.append(formatted_item)

            # 按报告期排序
            formatted_data.sort(key=lambda x: x['财报日期'], reverse=True)

            # 生成Markdown表格
            return format_markdown_report(
                f"{stock_code} 财务比率数据",
                table_data=formatted_data,
                footnote=f"💡 显示 {len(formatted_data)} 条财务比率数据",
            )

        except Exception as e:
            logger.error(f"获取财务比率数据时出错: {e}")
            return f"获取财务比率数据失败: {str(e)}"

    logger.info("财务分析工具已注册")