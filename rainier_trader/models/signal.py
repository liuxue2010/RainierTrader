from dataclasses import dataclass


@dataclass
class Indicators:
    sma_20: float | None
    sma_50: float | None
    sma_200: float | None
    rsi: float | None
    macd: float | None
    macd_signal: float | None
    macd_hist: float | None
    bb_upper: float | None
    bb_mid: float | None
    bb_lower: float | None


@dataclass
class Decision:
    action: str        # "buy" | "sell" | "hold"
    confidence: float  # 0.0 - 1.0
    reasoning: str
