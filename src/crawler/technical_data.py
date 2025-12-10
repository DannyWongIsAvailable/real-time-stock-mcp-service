from src.crawler.base_crawler import EastMoneyBaseSpider

import requests
from typing import List, Optional

class KlineSpider(EastMoneyBaseSpider):
    """
    K线数据爬虫

    使用示例：
        spider = KlineSpider()
        klines = spider.get_klines("300750", beg="20251101", end="20251130")
    """

    BASE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

    # K线周期常量
    KLT_1MIN = 1
    KLT_5MIN = 5
    KLT_15MIN = 15
    KLT_30MIN = 30
    KLT_60MIN = 60
    KLT_DAY = 101
    KLT_WEEK = 102
    KLT_MONTH = 103

    # 复权方式常量
    FQT_NONE = 0  # 不复权
    FQT_FORWARD = 1  # 前复权
    FQT_BACKWARD = 2  # 后复权

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = 20,
    ):
        super().__init__(session, timeout)
        self.headers["Referer"] = "https://quote.eastmoney.com/"

    def get_klines(
            self,
            stock_code: str,
            beg: str = "19000101",
            end: str = "20500101",
            klt: int = KLT_DAY,
            fqt: int = FQT_FORWARD,
    ) -> List[str]:
        """
        获取 K 线数据

        :param stock_code: 股票代码，要在数字后加上交易所代码，格式如688041.SH
        :param beg: 开始日期 YYYYMMDD
        :param end: 结束日期 YYYYMMDD
        :param klt: K线周期（使用 KLT_* 常量）
        :param fqt: 复权方式（使用 FQT_* 常量）
        :return: K线数据列表
        """
        secid = self.format_secid(stock_code)

        params = {
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "beg": beg,
            "end": end,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "rtntype": "6",
            "secid": secid,
            "klt": str(klt),
            "fqt": str(fqt),
        }

        data = self._get_json(self.BASE_URL, params)

        if not data.get("data"):
            raise RuntimeError(f"{secid}响应无 data 字段: {data}")

        klines = data["data"].get("klines")
        if klines is None:
            raise RuntimeError(f"{secid}响应无 klines 字段: {data}")

        return klines

# ==================== 使用示例 ====================
if __name__ == "__main__":

    # 获取 K 线
    spider = KlineSpider()
    klines = spider.get_klines(
        "300750.SZ",
        beg="20251123",
        end="20251128",
        klt=KlineSpider.KLT_DAY,
        fqt=KlineSpider.FQT_FORWARD,
    )
    print(f"K线数据 ({len(klines)} 条):")
    for line in klines:
        print(f"  {line}")