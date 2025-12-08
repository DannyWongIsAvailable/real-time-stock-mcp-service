from src.crawler.financial_analysis import FinancialAnalysisCrawler

# 测试营业总收入数据
# print("\n测试营业总收入数据:")
financial_analysis_crawler = FinancialAnalysisCrawler()
# operating_revenue_data = financial_analysis_crawler.get_operating_revenue("688041.SH")
# print(operating_revenue_data)



latest_report_date = financial_analysis_crawler.get_latest_report_dates("300750.SZ")
print("Latest report date for 300750.SZ:", latest_report_date)

get_industry_profit_comparison = financial_analysis_crawler.get_industry_profit_comparison("300750.SZ")
print("Industry profit comparison for 300750.SZ:", get_industry_profit_comparison)