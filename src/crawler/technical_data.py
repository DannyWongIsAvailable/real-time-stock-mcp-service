from src.crawler.base_crawler import EastMoneyBaseSpider

import requests
from typing import List, Optional, Dict, Any

class KlineSpider(EastMoneyBaseSpider):
    """
    K线数据爬虫

    使用示例：
        spider = KlineSpider()
        klines = spider.get_klines("300750", beg="20251101", end="20251130")
    """

    BASE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    TECHNICAL_INDICATORS_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

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
        获取 K 线数据，支持A股，H股，大盘

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

    def get_technical_indicators(
            self,
            stock_code: str,
            page_size: int = 30
    ) -> List[Dict[Any, Any]]:
        """
        获取技术指标数据

        :param stock_code: 股票代码，如300750（不包含交易所代码）
        :param page_size: 返回数据条数，默认为30条
        :return: 技术指标数据列表
        """
        # 移除股票代码中的交易所部分（如果存在）
        if '.' in stock_code:
            stock_code = stock_code.split('.')[0]

        # 生成 callback 参数
        callback = self._generate_callback()

        params = {
            "callback": callback,
            "filter": f'(SECURITY_CODE="{stock_code}")',
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "reportName": "PRT_STOCK_MACD_PK",
            "sortColumns": "TRADEDATE",
            "sortTypes": "-1",
            "pageSize": str(page_size),
            "_": str(self._timestamp_ms())
        }

        response = self._get_jsonp(self.TECHNICAL_INDICATORS_URL, params)

        if not response or not response.get("result"):
            raise RuntimeError(f"获取技术指标数据失败: {response}")

        data = response["result"].get("data")
        if data is None:
            raise RuntimeError(f"响应无 data 字段: {response}")

        return data

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
        
    # 获取技术指标
    try:
        technical_data = spider.get_technical_indicators("300750", 10)
        print(f"\\n技术指标数据 ({len(technical_data)} 条):")
        for item in technical_data:
            print(f"  日期: {item['TRADEDATE']}, MACD: {item['MACD']}, RSI1: {item['RSI1']}")
    except Exception as e:
        print(f"获取技术指标数据出错: {e}")