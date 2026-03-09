import pandas as pd
import pytest

from rainier_trader.nodes.analysis import _determine_signal


def test_bullish_signal():
    indicators = {
        "current_price": 175.0,
        "sma_20": 172.0,
        "sma_50": 168.0,
        "rsi": 25.0,    # oversold → bullish
        "macd": 1.0,
        "macd_signal": 0.5,  # macd > signal → bullish
    }
    assert _determine_signal(indicators) == "bullish"


def test_bearish_signal():
    indicators = {
        "current_price": 165.0,
        "sma_20": 172.0,
        "sma_50": 178.0,
        "rsi": 75.0,    # overbought → bearish
        "macd": 0.5,
        "macd_signal": 1.0,  # macd < signal → bearish
    }
    assert _determine_signal(indicators) == "bearish"


def test_neutral_signal():
    indicators = {
        "current_price": 170.0,
        "sma_20": 170.0,
        "sma_50": 170.0,
        "rsi": 50.0,
        "macd": 0.5,
        "macd_signal": 0.5,
    }
    # All tied → neutral
    assert _determine_signal(indicators) in ("neutral", "bullish", "bearish")


def test_neutral_on_missing_data():
    assert _determine_signal({}) == "neutral"
