import requests
from typing import Any, Dict, List, Optional

from stock_mcp.crawler.base_crawler import MultiSourceBaseSpider
from stock_mcp.crawler.technical_data import KlineSpider


class RealTimeDataSpider(MultiSourceBaseSpider):
    """
    实时股票数据爬虫。

    - 东方财富和雪球分别使用独立 Session、请求头及 Cookie；
    - 东方财富 Cookie 从构造参数或环境变量 EASTMONEY_COOKIE 读取；
    - 雪球 Cookie 从构造参数或环境变量 XUEQIU_COOKIE 读取。
    """

    MARKET_INDEX_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    XUEQIU_QUOTE_URL = "https://stock.xueqiu.com/v5/stock/quote.json"
    EASTMONEY_KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: Optional[int] = None,
            xueqiu_session: Optional[requests.Session] = None,
            xueqiu_cookie: Optional[str] = None,
    ):
        super().__init__(
            eastmoney_session=session,
            xueqiu_session=xueqiu_session,
            timeout=timeout,
            xueqiu_cookie=xueqiu_cookie,
        )
        self._xueqiu_session_ready = False

    def _ensure_xueqiu_session(self) -> None:
        if self._xueqiu_session_ready:
            return
        resp = self._xueqiu_get(
            "https://xueqiu.com/",
            headers={"Referer": "https://xueqiu.com/"},
        )
        resp.raise_for_status()
        self._xueqiu_session_ready = True

    def get_xueqiu_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """获取雪球实时行情。"""
        xueqiu_symbol = KlineSpider._format_xueqiu_symbol(symbol)
        self._ensure_xueqiu_session()

        params = {
            "symbol": xueqiu_symbol,
            "extend": "detail",
        }
        resp = self._xueqiu_get(
            self.XUEQIU_QUOTE_URL,
            params=params,
            headers={"Referer": f"https://xueqiu.com/S/{xueqiu_symbol}"},
        )
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("error_code") not in (0, None, "0"):
            raise RuntimeError(
                f"{xueqiu_symbol} 请求失败: "
                f"{payload.get('error_description') or payload}"
            )

        data = payload.get("data")
        if not data:
            raise RuntimeError(f"{xueqiu_symbol} 响应无 data 字段: {payload}")
        return data

    def get_eastmoney_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """获取东方财富实时/最新日 K 数据。"""
        params = {
            "secid": self.format_secid(symbol),
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": "19000101",
            "end": "20500101",
            "rtntype": "6",
            "lmt": "1",
            "_": str(self._timestamp_ms()),
        }

        resp = self._eastmoney_get(
            self.EASTMONEY_KLINE_URL,
            params=params,
            headers={"Referer": "https://quote.eastmoney.com/"},
        )
        resp.raise_for_status()
        payload = resp.json()

        data = payload.get("data") if isinstance(payload, dict) else None
        if not data:
            raise RuntimeError(f"获取东方财富实时行情失败: {payload}")

        if not data.get("klines"):
            raise RuntimeError(f"东方财富响应无有效 klines 字段: {payload}")
        return data

    def get_real_time_market_indices(self) -> List[Dict]:
        """获取东方财富实时大盘指数。"""
        params = {
            "ut": "13697a1cc677c8bfa9a496437bfef419",
            "fields": "f1,f2,f3,f4,f12,f13,f14",
            "secids": (
                "1.000001,1.000016,1.000300,1.000003,1.000688,"
                "0.399001,0.399006,0.399106,0.399003"
            ),
            "_": str(self._timestamp_ms()),
        }

        response = self._eastmoney_get_json(self.MARKET_INDEX_URL, params=params)
        rc = response.get("rc", -1)
        if rc != 0:
            raise RuntimeError(
                f"获取大盘指数数据失败: rc={rc}, response={response}"
            )

        return response.get("data", {}).get("diff", [])


if __name__ == "__main__":
    spider = RealTimeDataSpider()

    try:
        print("雪球实时行情:")
        print(spider.get_xueqiu_real_time_data("601127.SH"))
    except Exception as exc:
        print("雪球实时行情失败:", exc)

    try:
        print("\n东方财富实时/最新行情:")
        print(spider.get_eastmoney_real_time_data("601127.SH"))
    except Exception as exc:
        print("东方财富实时/最新行情失败:", exc)

    try:
        print("\n东方财富大盘指数:")
        print(spider.get_real_time_market_indices())
    except Exception as exc:
        print("东方财富大盘指数失败:", exc)
