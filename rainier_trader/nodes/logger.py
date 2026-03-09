import logging
from datetime import datetime

from rainier_trader.core.state import TradingState
from rainier_trader.storage.database import Database

logger = logging.getLogger(__name__)


def _build_log_entry(state: TradingState) -> dict:
    order = state.get("order_result") or {}
    return {
        "timestamp": state.get("timestamp", datetime.utcnow().isoformat()),
        "symbol": state["symbol"],
        "action": state.get("action", "hold"),
        "signal": state.get("technical_signal", "neutral"),
        "confidence": state.get("confidence", 0.0),
        "reasoning": state.get("reasoning", ""),
        "risk_approved": int(state.get("risk_approved", False)),
        "risk_note": state.get("risk_note", ""),
        "order_id": order.get("id"),
        "quantity": order.get("qty"),
        "price": state.get("current_price"),
        "total_value": (order.get("qty") or 0) * (state.get("current_price") or 0),
        "status": state.get("execution_status", "skipped"),
    }


def log_trade(state: TradingState) -> dict:
    entry = _build_log_entry(state)
    db = Database()
    db.insert_trade(entry)
    logger.info(f"{state['symbol']}: trade logged — {entry['action']} {entry['status']}")
    return {"log_entry": entry}


def log_skip(state: TradingState) -> dict:
    entry = _build_log_entry(state)
    entry["status"] = "skipped"
    db = Database()
    db.insert_trade(entry)
    logger.debug(f"{state['symbol']}: skip logged")
    return {"log_entry": entry}
