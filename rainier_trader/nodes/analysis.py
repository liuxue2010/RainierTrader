import logging

import pandas as pd
import pandas_ta as ta

from rainier_trader.core.state import TradingState

logger = logging.getLogger(__name__)


def analyze_indicators(state: TradingState) -> dict:
    symbol = state["symbol"]
    df = pd.DataFrame(state["price_data"])

    if len(df) < 50:
        logger.warning(f"{symbol}: insufficient data for indicators ({len(df)} bars)")
        return {"indicators": {}, "technical_signal": "neutral"}

    # Calculate indicators
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.bbands(length=20, std=2, append=True)

    last = df.iloc[-1]

    def get(col: str) -> float | None:
        val = last.get(col)
        return float(val) if val is not None and not pd.isna(val) else None

    indicators = {
        "current_price": state["current_price"],
        "sma_20": get("SMA_20"),
        "sma_50": get("SMA_50"),
        "sma_200": get("SMA_200"),
        "rsi": get("RSI_14"),
        "macd": get("MACD_12_26_9"),
        "macd_signal": get("MACDs_12_26_9"),
        "macd_hist": get("MACDh_12_26_9"),
        "bb_upper": get("BBU_20_2.0"),
        "bb_mid": get("BBM_20_2.0"),
        "bb_lower": get("BBL_20_2.0"),
    }

    signal = _determine_signal(indicators)
    logger.info(f"{symbol}: signal={signal}, RSI={indicators['rsi']}")
    return {"indicators": indicators, "technical_signal": signal}


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
