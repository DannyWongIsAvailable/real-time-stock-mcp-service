"""
K线数据工具
src/mcp_tools/kline_data.py
提供K线数据查询和分析功能
"""
import logging
from typing import List, Optional, Dict
from mcp.server.fastmcp import FastMCP
from ..data_source_interface import FinancialDataInterface
from ..utils.utils import format_number
from ..utils.markdown_formatter import format_list_to_markdown_table

logger = logging.getLogger(__name__)


def parse_kline_data(klines: List[str]) -> List[Dict]:
    """
    解析K线原始数据字符串

    Args:
        klines: K线原始数据字符串列表

    Returns:
        解析后的K线数据字典列表
    """
    result = []
    for kline in klines:
        fields = kline.split(",")
        if len(fields) >= 11:
            result.append({
                "date": fields[0],           # 日期
                "open": float(fields[1]),    # 开盘
                "close": float(fields[2]),   # 收盘
                "high": float(fields[3]),    # 最高
                "low": float(fields[4]),     # 最低
                "volume": int(fields[5]),    # 成交量
                "amount": float(fields[6]),  # 成交额
                "amplitude": float(fields[7]), # 振幅
                "change_percent": float(fields[8]), # 涨跌幅
                "change_amount": float(fields[9]),  # 涨跌额
                "turnover_rate": float(fields[10])  # 换手率
            })
    return result


def calculate_ma(data: List[float], period: int) -> List[Optional[float]]:
    """计算移动平均线（MA）"""
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(None)
        else:
            ma_value = sum(data[i - period + 1:i + 1]) / period
            result.append(round(ma_value, 2))
    return result


def calculate_ema(data: List[Optional[float]], period: int) -> List[Optional[float]]:
    """计算指数移动平均线（EMA）"""
    result = []
    multiplier = 2 / (period + 1)

    ema = None
    start_idx = 0
    for i, value in enumerate(data):
        if value is not None:
            ema = value
            start_idx = i
            break

    for i in range(start_idx):
        result.append(None)

    result.append(ema)

    for i in range(start_idx + 1, len(data)):
        if data[i] is not None:
            ema = (data[i] - ema) * multiplier + ema
            result.append(ema)
        else:
            result.append(None)

    return result


def calculate_macd(closes: List[float], fast: int = 12, slow: int = 26, dea_period: int = 9) -> Dict[str, List[Optional[float]]]:
    """计算 MACD 指标"""
    length = len(closes)
    if length == 0:
        return {"DIF": [], "DEA": [], "MACD": []}

    ema_fast = calculate_ema(closes, fast)
    ema_slow = calculate_ema(closes, slow)

    dif: List[Optional[float]] = []
    for i in range(length):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            dif_value = ema_fast[i] - ema_slow[i]
            dif.append(dif_value)
        else:
            dif.append(None)

    dea: List[Optional[float]] = calculate_ema(dif, dea_period)

    macd_bar: List[Optional[float]] = []
    for i in range(length):
        if dif[i] is not None and dea[i] is not None:
            macd_value = 2 * (dif[i] - dea[i])
            macd_bar.append(round(macd_value, 2))
        else:
            macd_bar.append(None)

    dif_rounded = [round(x, 2) if x is not None else None for x in dif]
    dea_rounded = [round(x, 2) if x is not None else None for x in dea]

    return {"DIF": dif_rounded, "DEA": dea_rounded, "MACD": macd_bar}


def calculate_rsi(closes: List[float], periods: List[int] = [6, 12, 24]) -> Dict:
    """计算RSI指标（Wilder 平滑版本）"""
    result: Dict[str, List[Optional[float]]] = {}
    n = len(closes)

    if n == 0:
        for period in periods:
            result[f"rsi{period}"] = []
        return result

    changes: List[float] = [0.0] * n
    gains: List[float] = [0.0] * n
    losses: List[float] = [0.0] * n

    for i in range(1, n):
        change = closes[i] - closes[i - 1]
        changes[i] = change
        if change > 0:
            gains[i] = change
            losses[i] = 0.0
        else:
            gains[i] = 0.0
            losses[i] = -change

    for period in periods:
        rsi_values: List[Optional[float]] = [None] * n

        if period <= 0 or n <= period:
            result[f"rsi{period}"] = rsi_values
            continue

        sum_gain = sum(gains[1:period + 1])
        sum_loss = sum(losses[1:period + 1])

        avg_gain = sum_gain / period
        avg_loss = sum_loss / period

        if avg_loss == 0:
            rsi_values[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values[period] = round(rsi, 2)

        for i in range(period + 1, n):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            if avg_loss == 0:
                rsi_values[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values[i] = round(rsi, 2)

        result[f"rsi{period}"] = rsi_values

    return result


def calculate_kdj(highs: List[float], lows: List[float], closes: List[float],
                   period: int = 9, k_period: int = 3, d_period: int = 3) -> Dict:
    """计算KDJ指标"""
    rsv_list = []

    for i in range(len(closes)):
        if i < period - 1:
            rsv_list.append(None)
        else:
            period_high = max(highs[i - period + 1:i + 1])
            period_low = min(lows[i - period + 1:i + 1])

            if period_high == period_low:
                rsv = 50
            else:
                rsv = (closes[i] - period_low) / (period_high - period_low) * 100

            rsv_list.append(rsv)

    k_values = []
    k = 50
    for rsv in rsv_list:
        if rsv is None:
            k_values.append(None)
        else:
            k = (k * (k_period - 1) + rsv) / k_period
            k_values.append(round(k, 2))

    d_values = []
    d = 50
    for k_val in k_values:
        if k_val is None:
            d_values.append(None)
        else:
            d = (d * (d_period - 1) + k_val) / d_period
            d_values.append(round(d, 2))

    j_values = []
    for i in range(len(k_values)):
        if k_values[i] is None or d_values[i] is None:
            j_values.append(None)
        else:
            j = 3 * k_values[i] - 2 * d_values[i]
            j_values.append(round(j, 2))

    return {'k': k_values, 'd': d_values, 'j': j_values}


def register_kline_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册K线数据相关工具

    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

    @app.tool()
    def get_kline(
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d"
    ) -> str:
        """
        获取历史K线数据

        获取指定股票在指定日期范围内的K线数据。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            K线数据的Markdown表格

        Examples:
            - get_kline("300750.SZ", "2024-01-01", "2024-01-31")
            - get_kline("300750.SZ", "2024-10-01", "2024-10-31", "w")
        """
        try:
            logger.info(f"获取K线: {stock_code}, {start_date} 至 {end_date}, 频率: {frequency}")

            # 从数据源获取原始数据
            raw_klines = data_source.get_historical_k_data(stock_code, start_date, end_date, frequency)

            if not raw_klines:
                return f"未找到股票代码 '{stock_code}' 在 {start_date} 至 {end_date} 的K线数据"

            # 解析原始数据
            kline_data = parse_kline_data(raw_klines)

            # 格式化数据
            formatted_data = []
            for k in kline_data:
                open_price = k.get('open', 0)
                close_price = k.get('close', 0)
                high_price = k.get('high', 0)
                low_price = k.get('low', 0)
                volume = k.get('volume', 0)
                amount = k.get('amount', 0)
                change_pct = k.get('change_percent', 0)
                amplitude = k.get('amplitude', 0)
                change_amount = k.get('change_amount', 0)
                turnover_rate = k.get('turnover_rate', 0)

                # 计算 K 线状态
                if close_price > open_price:
                    status = "上涨（阳线）"
                elif close_price < open_price:
                    status = "下跌（阴线）"
                else:
                    status = "平盘（十字星）"

                formatted_data.append({
                    '日期': k.get('date', ''),
                    'K线状态': status,
                    '开盘': format_number(open_price),
                    '收盘': format_number(close_price),
                    '最高': format_number(high_price),
                    '最低': format_number(low_price),
                    '涨跌幅': f"{'+' if change_pct > 0 else ''}{change_pct:.2f}%",
                    '成交量': format_number(volume, 0),
                    '成交额': format_number(amount, 0),
                    '振幅': f"{amplitude:.2f}%",
                    '涨跌额': format_number(change_amount),
                    '换手率': f"{turnover_rate:.2f}%"
                })

            table = format_list_to_markdown_table(formatted_data)
            note = f"\n\n💡 显示 {len(formatted_data)} 条K线数据，频率: {frequency}"
            return f"## {stock_code} K线数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"获取K线时出错: {e}")
            return f"获取K线失败: {str(e)}"

    @app.tool()
    def get_technical_indicators(
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d"
    ) -> str:
        """
        获取技术指标数据

        获取指定股票在指定日期范围内的技术指标数据。

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            frequency: K线周期，可选值: "d"(日), "w"(周), "m"(月), "5"(5分钟), "15"(15分钟), "30"(30分钟), "60"(60分钟)

        Returns:
            技术指标数据的Markdown表格

        Examples:
            - get_technical_indicators("300750.SZ", "2024-01-01", "2024-01-31")
            - get_technical_indicators("300750.SZ", "2024-10-01", "2024-10-31", "w")
        """
        try:
            logger.info(f"获取技术指标: {stock_code}, {start_date} 至 {end_date}, 频率: {frequency}")

            # 自动将开始日期往前推60天以获得更准确的技术指标数据
            from datetime import datetime, timedelta
            extended_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=60)).strftime("%Y-%m-%d")

            # 从数据源获取原始数据（使用扩展后的日期范围）
            raw_klines = data_source.get_technical_indicators(stock_code, extended_start_date, end_date, frequency)

            if not raw_klines:
                return f"未找到股票代码 '{stock_code}' 在 {start_date} 至 {end_date} 的K线数据"

            # 解析K线数据
            k_data = parse_kline_data(raw_klines)

            # 过滤出用户请求的日期范围内的数据用于最终显示
            filtered_k_data = [item for item in k_data if item['date'] >= start_date]

            # 提取数据用于计算技术指标（使用扩展后的数据）
            closes = [item['close'] for item in k_data]
            highs = [item['high'] for item in k_data]
            lows = [item['low'] for item in k_data]

            # 计算技术指标
            ma5 = calculate_ma(closes, 5)
            ma10 = calculate_ma(closes, 10)
            ma20 = calculate_ma(closes, 20)
            ma60 = calculate_ma(closes, 60)

            macd_data = calculate_macd(closes)
            rsi_data = calculate_rsi(closes)
            kdj_data = calculate_kdj(highs, lows, closes)

            # 格式化数据（仅使用过滤后的数据）
            formatted_data = []
            # 计算需要跳过的数据量
            skip_count = len(k_data) - len(filtered_k_data)
            
            for i, item in enumerate(filtered_k_data):
                idx = i + skip_count  # 使用原始索引以获取正确的技术指标值
                formatted_data.append({
                    '日期': item['date'],
                    'MA5': format_number(ma5[idx]),
                    'MA10': format_number(ma10[idx]),
                    'MA20': format_number(ma20[idx]),
                    'MA60': format_number(ma60[idx]),
                    'DIF': format_number(macd_data['DIF'][idx]),
                    'DEA': format_number(macd_data['DEA'][idx]),
                    'MACD柱': format_number(macd_data['MACD'][idx]),
                    'RSI6': format_number(rsi_data['rsi6'][idx]),
                    'RSI12': format_number(rsi_data['rsi12'][idx]),
                    'RSI24': format_number(rsi_data['rsi24'][idx]),
                    'KDJ_K': format_number(kdj_data['k'][idx]),
                    'KDJ_D': format_number(kdj_data['d'][idx]),
                    'KDJ_J': format_number(kdj_data['j'][idx])
                })

            table = format_list_to_markdown_table(formatted_data)
            note = f"\n\n💡 显示 {len(formatted_data)} 条技术指标数据，频率: {frequency}"
            return f"## {stock_code} 技术指标数据\n\n{table}{note}"

        except Exception as e:
            logger.error(f"获取技术指标时出错: {e}")
            return f"获取技术指标失败: {str(e)}"