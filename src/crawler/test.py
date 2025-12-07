from src.crawler.financial_analysis import FinancialAnalysisCrawler

# 测试营业总收入数据
print("\n测试营业总收入数据:")
financial_analysis_crawler = FinancialAnalysisCrawler()
operating_revenue_data = financial_analysis_crawler.get_operating_revenue("688041.SH")
print(operating_revenue_data)