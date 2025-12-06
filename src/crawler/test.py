from src.crawler.fundamental_data import FundamentalDataCrawler

# 测试获取主营业务构成
crawler = FundamentalDataCrawler()
r = crawler.get_main_business("000021.SZ", "2025-06-30")
print("主营业务构成:")
print(r)

# 测试获取报告日期
report_dates = crawler.get_report_dates("000021.SZ")
print("\n报告日期:")
print(report_dates)