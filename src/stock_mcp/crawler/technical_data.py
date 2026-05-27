from stock_mcp.crawler.base_crawler import EastMoneyBaseSpider

import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

_CN_TZ = timezone(timedelta(hours=8))

class KlineSpider(EastMoneyBaseSpider):
    """
    K线数据爬虫

    使用示例：
        spider = KlineSpider()
        klines = spider.get_klines("300750", beg="20251101", end="20251130")
    """

    BASE_URL = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
    TECHNICAL_INDICATORS_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    PKYD_URL = "https://push2.eastmoney.com/api/qt/pkyd/get"  # 盘口异动API
    XUEQIU_INDICATOR = "kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance"

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
        self._xueqiu_session_ready = False

    def _ensure_xueqiu_session(self) -> None:
        if self._xueqiu_session_ready:
            return
        self.session.get(
            "https://xueqiu.com/",
            headers={
                **self.headers,
                "Referer": "https://xueqiu.com/",
            },
            timeout=self.timeout,
        )
        self._xueqiu_session_ready = True

    @staticmethod
    def _format_xueqiu_symbol(stock_code: str) -> str:
        code = stock_code.strip().upper()
        if "." in code:
            left, right = code.split(".", maxsplit=1)
            if right == "SH":
                return f"SH{left}"
            if right == "SZ":
                return f"SZ{left}"
        if code.isdigit():
            if code.startswith("6"):
                return f"SH{code}"
            return f"SZ{code}"
        raise ValueError(f"无法解析股票代码: {stock_code}")

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        normalized = date_str.replace("-", "").replace(" ", "").strip()
        return datetime.strptime(normalized, "%Y%m%d").replace(tzinfo=_CN_TZ)

    @staticmethod
    def _date_to_ms(date_str: str, end_of_day: bool = True) -> int:
        dt = KlineSpider._parse_date(date_str)
        if end_of_day:
            dt = dt.replace(hour=15, minute=0, second=0, microsecond=0)
        return int(dt.timestamp() * 1000)

    @staticmethod
    def _klt_to_period(klt: int) -> str:
        period_map = {
            KlineSpider.KLT_1MIN: "1m",
            KlineSpider.KLT_5MIN: "5m",
            KlineSpider.KLT_15MIN: "15m",
            KlineSpider.KLT_30MIN: "30m",
            KlineSpider.KLT_60MIN: "60m",
            KlineSpider.KLT_DAY: "day",
            KlineSpider.KLT_WEEK: "week",
            KlineSpider.KLT_MONTH: "month",
        }
        return period_map.get(klt, "day")

    @staticmethod
    def _fqt_to_type(fqt: int) -> str:
        type_map = {
            KlineSpider.FQT_NONE: "normal",
            KlineSpider.FQT_FORWARD: "before",
            KlineSpider.FQT_BACKWARD: "after",
        }
        return type_map.get(fqt, "before")

    @staticmethod
    def _calc_count(beg: str, end: str) -> int:
        start = KlineSpider._parse_date(beg)
        end_dt = KlineSpider._parse_date(end)
        days = max((end_dt - start).days + 1, 1)
        # 预留非交易日缓冲，单次最多拉 1023 根
        return -min(int(days * 1.5) + 10, 1023)

    @staticmethod
    def _rows_from_xueqiu(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        columns = data.get("column") or []
        items = data.get("item") or []
        return [dict(zip(columns, row)) for row in items]

    def get_klines(
            self,
            stock_code: str,
            beg: str = "19000101",
            end: str = "20500101",
            klt: int = KLT_DAY,
            fqt: int = FQT_FORWARD,
    ) -> List[Dict[str, Any]]:
        """
        获取 K 线数据（雪球 API），支持 A 股日线/周线/月线及分钟线

        :param stock_code: 股票代码，格式如 601127.SH
        :param beg: 开始日期 YYYYMMDD
        :param end: 结束日期 YYYYMMDD
        :param klt: K线周期（使用 KLT_* 常量）
        :param fqt: 复权方式（使用 FQT_* 常量）
        :return: K 线列表，每项为 {column: value} 字典
        """
        symbol = self._format_xueqiu_symbol(stock_code)
        self._ensure_xueqiu_session()

        end_anchor = end if end != "20500101" else datetime.now(_CN_TZ).strftime("%Y%m%d")
        params = {
            "symbol": symbol,
            "begin": str(self._date_to_ms(end_anchor)),
            "period": self._klt_to_period(klt),
            "type": self._fqt_to_type(fqt),
            "count": str(self._calc_count(beg, end_anchor)),
            "indicator": self.XUEQIU_INDICATOR,
        }

        resp = self.session.get(
            self.BASE_URL,
            params=params,
            headers={
                **self.headers,
                "Referer": f"https://xueqiu.com/S/{symbol}",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("error_code") not in (0, None):
            raise RuntimeError(
                f"{symbol} 请求失败: {payload.get('error_description') or payload}"
            )

        data = payload.get("data")
        if not data:
            raise RuntimeError(f"{symbol} 响应无 data 字段: {payload}")

        rows = self._rows_from_xueqiu(data)
        if not rows:
            return []

        start_ms = self._date_to_ms(beg, end_of_day=False)
        end_ms = self._date_to_ms(end_anchor, end_of_day=True)
        filtered = [
            row for row in rows
            if start_ms <= row.get("timestamp", 0) <= end_ms
        ]
        return filtered or rows

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

        # 获取MACD等技术指标数据
        macd_data = self._get_macd_data(stock_code, page_size)
        
        # 获取趋势量能等额外技术指标数据
        trend_data = self._get_trend_volume_data(stock_code, page_size)
        
        # 合并数据
        merged_data = self._merge_technical_data(macd_data, trend_data)
        
        return merged_data

    def get_intraday_changes(self, stock_code: str) -> List[str]:
        """
        获取分时图盘口异动数据

        :param stock_code: 股票代码，如"300274.SZ"
        :return: 盘口异动数据列表
        """
        secid = self.format_secid(stock_code)

        params = {
            "fields": "f1,f2,f3,f4,f5,f6,f7",
            "secids": secid,
            "lmt": "40",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "wbp2u": "1849325530509956|0|1|0|web",
            "cb": "quote_jp0"
        }

        response = self._get_jsonp(self.PKYD_URL, params)

        if not response or not response.get("data"):
            raise RuntimeError(f"获取盘口异动数据失败: {response}")

        pkyd_data = response["data"].get("pkyd")
        if pkyd_data is None:
            raise RuntimeError(f"响应无 pkyd 字段: {response}")

        return pkyd_data

    def _get_macd_data(self, stock_code: str, page_size: int) -> List[Dict[Any, Any]]:
        """
        获取MACD技术指标数据

        :param stock_code: 股票代码
        :param page_size: 返回数据条数
        :return: MACD技术指标数据列表
        """
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
            raise RuntimeError(f"获取MACD技术指标数据失败: {response}")

        data = response["result"].get("data")
        if data is None:
            raise RuntimeError(f"响应无 data 字段: {response}")

        return data

    def _get_trend_volume_data(self, stock_code: str, page_size: int) -> List[Dict[Any, Any]]:
        """
        获取趋势量能技术指标数据

        :param stock_code: 股票代码
        :param page_size: 返回数据条数
        :return: 趋势量能技术指标数据列表
        """
        # 生成 callback 参数
        callback = self._generate_callback()

        params = {
            "callback": callback,
            "filter": f'(SECURITY_CODE="{stock_code}")',
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "reportName": "RPT_STOCK_TRENDVOLUME_PK",
            "sortColumns": "TRADE_DATE",
            "sortTypes": "-1",
            "pageSize": str(page_size),
            "_": str(self._timestamp_ms())
        }

        response = self._get_jsonp(self.TECHNICAL_INDICATORS_URL, params)

        if not response or not response.get("result"):
            raise RuntimeError(f"获取趋势量能技术指标数据失败: {response}")

        data = response["result"].get("data")
        if data is None:
            raise RuntimeError(f"响应无 data 字段: {response}")

        return data

    def _merge_technical_data(self, macd_data: List[Dict], trend_data: List[Dict]) -> List[Dict[Any, Any]]:
        """
        合并不同来源的技术指标数据

        :param macd_data: MACD技术指标数据
        :param trend_data: 趋势量能技术指标数据
        :return: 合并后的技术指标数据
        """
        # 创建以日期为键的字典以便匹配数据
        trend_dict = {item.get('TRADE_DATE', item.get('TRADEDATE')): item for item in trend_data}
        
        merged_data = []
        for macd_item in macd_data:
            # 使用TRADEDATE作为主键
            trade_date = macd_item.get('TRADEDATE')
            merged_item = macd_item.copy()
            
            # 如果在趋势数据中找到匹配的日期，则合并数据
            if trade_date in trend_dict:
                trend_item = trend_dict[trade_date]
                # 添加趋势量能相关字段
                merged_item.update({
                    "AVG_PRICE": trend_item.get("AVG_PRICE"),
                    "AVG_AMOUNT_5DAYS": trend_item.get("AVG_AMOUNT_5DAYS"),
                    "DAILY_TRADE_60TD": trend_item.get("DAILY_TRADE_60TD"),
                    "PRESSURE_LEVEL": trend_item.get("PRESSURE_LEVEL"),
                    "SUPPORT_LEVEL": trend_item.get("SUPPORT_LEVEL"),
                    "WORDS_EXPLAIN": trend_item.get("WORDS_EXPLAIN")
                })
            
            merged_data.append(merged_item)
        
        return merged_data

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
    for row in klines:
        print(f"  {row}")
        
    # 获取技术指标
    try:
        technical_data = spider.get_technical_indicators("300750", 10)
        print(f"\\n技术指标数据 ({len(technical_data)} 条):")
        for item in technical_data:
            print(f"  日期: {item['TRADEDATE']}, MACD: {item['MACD']}, RSI1: {item['RSI1']}")
    except Exception as e:
        print(f"获取技术指标数据出错: {e}")