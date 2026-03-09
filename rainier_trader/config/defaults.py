DEFAULT_CONFIG = {
    "mode": "paper",
    "watchlist": ["AAPL", "MSFT", "NVDA"],
    "schedule": {
        "interval_minutes": 5,
        "market_hours_only": True,
    },
    "strategy": {
        "indicators": {
            "sma_fast": 20,
            "sma_slow": 50,
            "sma_trend": 200,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "bb_period": 20,
            "bb_std": 2,
        },
        "min_confidence": 0.6,
    },
    "risk": {
        "max_position_pct": 20,
        "max_positions": 5,
        "stop_loss_pct": 3,
        "take_profit_pct": 8,
        "daily_loss_limit_pct": 5,
        "min_cash_reserve_pct": 20,
    },
    "orders": {
        "type": "market",
        "time_in_force": "day",
    },
    "llm": {
        "model": "claude-sonnet-4-6",
        "temperature": 0.3,
        "max_tokens": 1000,
    },
    "logging": {
        "level": "INFO",
        "file": "logs/rainier.log",
    },
}
