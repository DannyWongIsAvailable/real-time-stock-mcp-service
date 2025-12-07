from src.crawler.valuation_data import ValuationDataCrawler
from src.crawler.real_time_data import  RealTimeDataSpider
from src.crawler.technical_data import KlineSpider

# 测试估值分析数据
valuation_crawler = ValuationDataCrawler()

# 测试默认参数（市盈率TTM，5年周期）
# print("测试默认参数（市盈率TTM，5年周期）:")
# valuation_data = valuation_crawler.get_valuation_analysis("688041.SH")
# print(valuation_data)
#
# # 测试市净率MRQ，3年周期
# print("\n测试市净率MRQ，3年周期:")
# pb_data = valuation_crawler.get_valuation_analysis(
#     "688041.SH",
#     ValuationDataCrawler.INDICATOR_TYPE_PB_MRQ,
#     ValuationDataCrawler.DATE_TYPE_3YEAR
# )
# print(pb_data)
#
# # 测试市销率TTM，10年周期
# print("\n测试市销率TTM，10年周期:")
# ps_data = valuation_crawler.get_valuation_analysis(
#     "688041.SH",
#     ValuationDataCrawler.INDICATOR_TYPE_PS_TTM,
#     ValuationDataCrawler.DATE_TYPE_10YEAR
# )
# print(ps_data)

# 测试机构评级功能
# print("\n测试机构评级功能:")
# # 设置正确的日期范围（开始日期应该早于结束日期）
# start_date = "2025-10-23"
# end_date = "2025-12-07"
# institutional_rating_data = valuation_crawler.get_institutional_rating("688041", start_date, end_date)
# print(institutional_rating_data)
#
# real_time_data_spider = RealTimeDataSpider()
# #    获取实时股票数据
# print("\n获取实时股票数据:")
# real_time_data = real_time_data_spider.get_real_time_data("01810")
# print(real_time_data)

# 获取k线
k_line = KlineSpider().get_klines("300750", beg="20251123", end="20251128", klt=KlineSpider.KLT_DAY, fqt=KlineSpider.FQT_FORWARD)

print(k_line)
