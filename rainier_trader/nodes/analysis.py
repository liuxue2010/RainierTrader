import logging

import pandas as pd
import ta

from rainier_trader.core.state import TradingState

logger = logging.getLogger(__name__)


def analyze_indicators(state: TradingState) -> dict:
    symbol = state["symbol"]
    df = pd.DataFrame(state["price_data"])

    if len(df) < 50:
        logger.warning(f"{symbol}: insufficient data for indicators ({len(df)} bars)")
        return {"indicators": {}, "technical_signal": "neutral"}

    close = df["close"]

    indicators = {
        "current_price": state["current_price"],
        "sma_20": _last(ta.trend.SMAIndicator(close, window=20).sma_indicator()),
        "sma_50": _last(ta.trend.SMAIndicator(close, window=50).sma_indicator()),
        "sma_200": _last(ta.trend.SMAIndicator(close, window=200).sma_indicator()),
        "rsi": _last(ta.momentum.RSIIndicator(close, window=14).rsi()),
    }

    macd = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
    indicators["macd"] = _last(macd.macd())
    indicators["macd_signal"] = _last(macd.macd_signal())
    indicators["macd_hist"] = _last(macd.macd_diff())

    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    indicators["bb_upper"] = _last(bb.bollinger_hband())
    indicators["bb_mid"] = _last(bb.bollinger_mavg())
    indicators["bb_lower"] = _last(bb.bollinger_lband())

    signal = _determine_signal(indicators)
    logger.info(f"{symbol}: signal={signal}, RSI={indicators['rsi']}")
    return {"indicators": indicators, "technical_signal": signal}


def _last(series: pd.Series) -> float | None:
    val = series.iloc[-1] if len(series) > 0 else None
    return float(val) if val is not None and not pd.isna(val) else None


def _determine_signal(ind: dict) -> str:
    bullish = 0
    bearish = 0

    rsi = ind.get("rsi")
    if rsi is not None:
        if rsi < 30:
            bullish += 1
        elif rsi > 70:
            bearish += 1

    macd = ind.get("macd")
    macd_signal = ind.get("macd_signal")
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            bullish += 1
        else:
            bearish += 1

    price = ind.get("current_price")
    sma_20 = ind.get("sma_20")
    sma_50 = ind.get("sma_50")
    if price and sma_20 and sma_50:
        if price > sma_20 > sma_50:
            bullish += 1
        elif price < sma_20 < sma_50:
            bearish += 1

    if bullish > bearish:
        return "bullish"
    elif bearish > bullish:
        return "bearish"
    return "neutral"
