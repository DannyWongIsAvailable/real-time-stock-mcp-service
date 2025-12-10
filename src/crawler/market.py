import requests
from typing import Dict, List, Optional
from .base_crawler import EastMoneyBaseSpider


class MarketSpider(EastMoneyBaseSpider):
    """
    市场板块行情爬虫类
    
    用于获取东方财富网的板块行情数据，包括行业板块、概念板块、地域板块等。
    """

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = None,
    ):
        super().__init__(session, timeout)
        self.base_url = "https://push2.eastmoney.com/api/qt/clist/get"

    def get_plate_quotation(self, plate_type: int = 2) -> List[Dict]:
        """
        获取板块行情数据
        
        :param plate_type: 板块类型参数
            - 1: 地域板块  
            - 2: 行业板块
            - 3: 概念板块
        :return: 板块行情数据列表
        """
        # 构建 fs 参数
        fs_param = f"m:90 t:{plate_type} f:!50"
        
        params = {
            "np": "1",
            "fltt": "1",
            "invt": "2",
            "cb": self._generate_callback(),
            "fs": fs_param,
            "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f20,f8,f104,f105,f128,f140,f141,f207,f208,f209,f136,f222",
            "fid": "f3",
            "pn": "1",
            "pz": "10",
            "po": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "dect": "1",
            "wbp2u": "|0|0|0|web",
            "_": str(self._timestamp_ms())
        }

        response = self._get_jsonp(self.base_url, params)
        
        if response and response.get("data") and response["data"].get("diff"):
            return response["data"]["diff"]
        else:
            return []

