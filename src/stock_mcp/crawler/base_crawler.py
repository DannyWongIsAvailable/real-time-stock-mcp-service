import importlib.util
import json
import os
import random
import re
import time
from abc import ABC
from typing import Any, Dict, Optional

import requests


class BaseCrawler(ABC):
    """行情爬虫公共基础能力，不绑定具体数据源。"""

    DEFAULT_TIMEOUT = 10

    def __init__(self, timeout: Optional[int] = None):
        self.timeout = timeout or self.DEFAULT_TIMEOUT

    @staticmethod
    def _parse_jsonp(text: str) -> Optional[Dict]:
        """解析 jQuery 风格 JSONP，允许末尾分号。"""
        match = re.search(r"^\w+\((.*)\);?$", text.strip(), re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _generate_callback() -> str:
        """生成 jQuery 风格 callback 名称。"""
        rand_part = random.randint(10**19, 10**20 - 1)
        ts = int(time.time() * 1000)
        return f"jQuery{rand_part}_{ts}"

    @staticmethod
    def _timestamp_ms() -> int:
        """当前时间戳（毫秒）。"""
        return int(time.time() * 1000)

    @staticmethod
    def _resolve_cookie(explicit: Optional[str], env_name: str) -> str:
        """优先使用构造参数，否则读取环境变量。"""
        if explicit is not None:
            return explicit.strip()
        return os.getenv(env_name, "").strip()


class EastMoneyBaseSpider(BaseCrawler):
    """
    东方财富请求基类。

    东方财富使用独立的 Session、请求头和 Cookie 容器，绝不与雪球混用。
    为兼容项目中已有子类，保留 self.session/self.headers/self.cookies 别名，
    这些别名只指向东方财富配置。

    Cookie 可通过：
    1. 构造参数 eastmoney_cookie；
    2. 环境变量 EASTMONEY_COOKIE。
    """

    EASTMONEY_DEFAULT_HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
        ),
    }

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: Optional[int] = None,
            eastmoney_cookie: Optional[str] = None,
    ):
        super().__init__(timeout)
        self._init_eastmoney(session, eastmoney_cookie)

    def _init_eastmoney(
            self,
            session: Optional[requests.Session] = None,
            eastmoney_cookie: Optional[str] = None,
    ) -> None:
        self.eastmoney_session = session or requests.Session()
        self.eastmoney_headers = self.EASTMONEY_DEFAULT_HEADERS.copy()
        self.eastmoney_cookies: Dict[str, str] = {}

        cookie_header = self._resolve_cookie(eastmoney_cookie, "EASTMONEY_COOKIE")
        if cookie_header:
            self.eastmoney_headers["Cookie"] = cookie_header

        # 向后兼容：旧子类中的 self.session/self.headers/self.cookies
        # 始终仅代表东方财富，雪球不会使用这些属性。
        self.session = self.eastmoney_session
        self.headers = self.eastmoney_headers
        self.cookies = self.eastmoney_cookies

    def _eastmoney_get(
            self,
            url: str,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            **kwargs: Any,
    ) -> requests.Response:
        """使用东方财富专属 Session 发起 GET。"""
        request_headers = self.eastmoney_headers.copy()
        if headers:
            request_headers.update(headers)

        kwargs.setdefault("cookies", self.eastmoney_cookies)
        kwargs.setdefault("timeout", self.timeout)
        return self.eastmoney_session.get(
            url,
            params=params,
            headers=request_headers,
            **kwargs,
        )

    # 兼容旧子类。
    def _get(
            self,
            url: str,
            params: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
    ) -> requests.Response:
        return self._eastmoney_get(url, params=params, **kwargs)

    def _eastmoney_get_json(
            self,
            url: str,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Dict:
        resp = self._eastmoney_get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """兼容旧代码：仅使用东方财富 Session。"""
        return self._eastmoney_get_json(url, params=params)

    def _get_jsonp(
            self,
            url: str,
            params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict]:
        """兼容旧代码：仅使用东方财富 Session。"""
        resp = self._eastmoney_get(url, params=params)
        resp.raise_for_status()
        return self._parse_jsonp(resp.text)

    @staticmethod
    def format_secid(stock_code: str) -> str:
        """
        将股票代码转换为东方财富 secid。

        示例：
        - 000977 / 000977.SZ -> 0.000977
        - 600000 / 600000.SH -> 1.600000
        - 01810 / 01810.HK   -> 116.01810
        """
        code = stock_code.strip().upper()

        if "." in code:
            left, right = code.split(".", maxsplit=1)

            if left in {"0", "1", "116"} and right.isdigit():
                return f"{left}.{right}"

            if right in {"SZ", "SH"}:
                market = "0" if right == "SZ" else "1"
                return f"{market}.{left}"

            if right == "HK":
                return f"116.{left.zfill(5)}"

        if code.isdigit():
            if code.startswith("6"):
                return f"1.{code}"
            if len(code) == 5:
                return f"116.{code}"
            return f"0.{code}"

        raise ValueError(f"无法解析股票代码: {stock_code}")


class XueqiuBaseSpider(BaseCrawler):
    """
    雪球请求基类。

    雪球使用独立的 Session、请求头和 CookieJar。Cookie 可通过：
    1. 构造参数 xueqiu_cookie；
    2. 环境变量 XUEQIU_COOKIE。

    不要把浏览器 Cookie 硬编码进源码。
    """
    XUEQIU_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
    )

    XUEQIU_NAVIGATION_HEADERS = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Pragma": "no-cache",
        "Priority": "u=0, i",
        "Sec-CH-UA": (
            '"Microsoft Edge";v="149", "Chromium";v="149", '
            '"Not)A;Brand";v="24"'
        ),
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": XUEQIU_USER_AGENT,
    }

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: Optional[int] = None,
            xueqiu_cookie: Optional[str] = None,
    ):
        super().__init__(timeout)
        self._init_xueqiu(session, xueqiu_cookie)

    @staticmethod
    def _supported_accept_encoding() -> str:
        """
        只声明当前 Python 环境实际能够解压的编码。

        浏览器抓包中虽包含 br/zstd，但 requests 若缺少对应解码库，
        强行声明会导致响应体无法解析。
        """
        encodings = ["gzip", "deflate"]
        if importlib.util.find_spec("brotli") or importlib.util.find_spec("brotlicffi"):
            encodings.append("br")
        if importlib.util.find_spec("zstandard"):
            encodings.append("zstd")
        return ", ".join(encodings)

    def _init_xueqiu(
            self,
            session: Optional[requests.Session] = None,
            xueqiu_cookie: Optional[str] = None,
    ) -> None:
        self.xueqiu_session = session or requests.Session()
        self.xueqiu_headers = self.XUEQIU_NAVIGATION_HEADERS.copy()
        self.xueqiu_headers["Accept-Encoding"] = self._supported_accept_encoding()

        cookie_header = self._resolve_cookie(xueqiu_cookie, "XUEQIU_COOKIE")
        if cookie_header:
            self.set_xueqiu_cookie(cookie_header)

    def build_xueqiu_headers(
            self,
            referer: Optional[str] = None,
            direct_navigation: bool = True,
    ) -> Dict[str, str]:
        """构造雪球请求头，不包含 Cookie 和 HTTP/2 伪标头。"""
        headers = self.xueqiu_headers.copy()

        if referer:
            headers["Referer"] = referer
            headers["Sec-Fetch-Site"] = "same-origin"
        else:
            headers.pop("Referer", None)
            headers["Sec-Fetch-Site"] = "none"

        if direct_navigation:
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-User"] = "?1"
            headers["Upgrade-Insecure-Requests"] = "1"
        else:
            headers["Sec-Fetch-Dest"] = "empty"
            headers["Sec-Fetch-Mode"] = "cors"
            headers.pop("Sec-Fetch-User", None)
            headers.pop("Upgrade-Insecure-Requests", None)

        return headers

    def set_xueqiu_cookie(self, cookie_header: str, clear_existing: bool = False) -> int:
        """
        将浏览器复制的 Cookie 字符串装入雪球专属 CookieJar。

        :return: 成功装入的 Cookie 数量。
        """
        if clear_existing:
            self.xueqiu_session.cookies.clear()

        count = 0
        for item in cookie_header.split(";"):
            item = item.strip()
            if not item or "=" not in item:
                continue
            name, value = item.split("=", 1)
            name = name.strip()
            value = value.strip()
            if not name:
                continue
            self.xueqiu_session.cookies.set(
                name,
                value,
                domain=".xueqiu.com",
                path="/",
            )
            count += 1
        return count

    def _xueqiu_get(
            self,
            url: str,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            **kwargs: Any,
    ) -> requests.Response:
        """使用雪球专属 Session 发起 GET。"""
        request_headers = self.xueqiu_headers.copy()
        if headers:
            request_headers.update(headers)

        kwargs.setdefault("timeout", self.timeout)
        return self.xueqiu_session.get(
            url,
            params=params,
            headers=request_headers,
            **kwargs,
        )


class MultiSourceBaseSpider(EastMoneyBaseSpider, XueqiuBaseSpider):
    """同时使用东方财富和雪球，但两套 Session/Headers/Cookies 完全隔离。"""

    def __init__(
            self,
            eastmoney_session: Optional[requests.Session] = None,
            xueqiu_session: Optional[requests.Session] = None,
            timeout: Optional[int] = None,
            eastmoney_cookie: Optional[str] = None,
            xueqiu_cookie: Optional[str] = None,
    ):
        BaseCrawler.__init__(self, timeout)
        EastMoneyBaseSpider._init_eastmoney(self, eastmoney_session, eastmoney_cookie)
        XueqiuBaseSpider._init_xueqiu(self, xueqiu_session, xueqiu_cookie)
