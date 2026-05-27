import requests
from typing import Dict, Any, Optional, List

from stock_mcp.crawler.base_crawler import EastMoneyBaseSpider
from stock_mcp.crawler.technical_data import KlineSpider


class RealTimeDataSpider(EastMoneyBaseSpider):
    """
    实时股票数据爬虫（雪球 API）
    """

    MARKET_INDEX_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    QUOTE_URL = "https://stock.xueqiu.com/v5/stock/quote.json"

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = None,
    ):
        super().__init__(session, timeout)
        self._xueqiu_session_ready = False

    def _ensure_xueqiu_session(self) -> None:
        if self._xueqiu_session_ready:
            return
        self.session.get(
            "https://xueqiu.com/",
            headers={**self.headers, "Referer": "https://xueqiu.com/"},
            timeout=self.timeout,
        )
        self._xueqiu_session_ready = True

    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票实时行情（雪球 quote.json）

        :param symbol: 股票代码，格式如 601127.SH
        :return: API 的 data 字段（含 market、quote、others、tags），不做重组
        """
        xueqiu_symbol = KlineSpider._format_xueqiu_symbol(symbol)
        self._ensure_xueqiu_session()

        params = {
            "symbol": xueqiu_symbol,
            "extend": "detail",
        }

        resp = self.session.get(
            self.QUOTE_URL,
            params=params,
            headers={
                **self.headers,
                "Referer": f"https://xueqiu.com/S/{xueqiu_symbol}",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("error_code") not in (0, None):
            raise RuntimeError(
                f"{xueqiu_symbol} 请求失败: {payload.get('error_description') or payload}"
            )

        data = payload.get("data")
        if not data:
            raise RuntimeError(f"{xueqiu_symbol} 响应无 data 字段: {payload}")

        return data

    def get_real_time_market_indices(self) -> List[Dict]:
        """
        获取实时大盘指数数据（东方财富）

        :return: 实时大盘指数数据列表
        """
        params = {
            "ut": "13697a1cc677c8bfa9a496437bfef419",
            "fields": "f1,f2,f3,f4,f12,f13,f14",
            "secids": "1.000001,1.000016,1.000300,1.000003,1.000688,0.399001,0.399006,0.399106,0.399003",
            "_": str(self._timestamp_ms()),
        }

        response = self._get_json(self.MARKET_INDEX_URL, params)
        rc = response.get("rc", -1)

        if rc != 0:
            raise Exception(f"获取大盘指数数据失败: rc={rc}")

        data = response.get("data", {})
        return data.get("diff", [])


if __name__ == "__main__":
    spider = RealTimeDataSpider()
    print(spider.get_real_time_data("601127.SH"))
