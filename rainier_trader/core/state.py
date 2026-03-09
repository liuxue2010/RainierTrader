from typing import TypedDict


class TradingState(TypedDict):
    # Input
    symbol: str
    timestamp: str

    # Market Data
    price_data: dict          # OHLCV bars
    current_price: float

    # Analysis
    indicators: dict          # MA, MACD, RSI, BOLL values
    technical_signal: str     # "bullish" | "bearish" | "neutral"

    # Decision
    action: str               # "buy" | "sell" | "hold"
    reasoning: str            # LLM's explanation
    confidence: float         # 0.0 - 1.0

    # Risk Check
    risk_approved: bool
    risk_note: str            # Why rejected if not approved

    # Execution
    order_result: dict | None  # Alpaca order response
    execution_status: str      # "executed" | "skipped" | "failed"

    # Logging
    log_entry: dict           # Complete audit record
