import logging

from rainier_trader.core.state import TradingState

logger = logging.getLogger(__name__)


async def execute_order(state: TradingState) -> dict:
    from rainier_trader.clients.alpaca_client import AlpacaClient
    from rainier_trader.config.settings import load_settings

    settings = load_settings()
    broker = AlpacaClient(settings.alpaca_api_key, settings.alpaca_secret_key, paper=settings.is_paper)
    risk = settings.risk
    symbol = state["symbol"]
    action = state["action"]

    try:
        account = await broker.get_account()
        positions = await broker.get_positions()

        if action == "buy":
            # Size position: up to max_position_pct of equity, but respect cash reserve
            max_spend = account.equity * (risk.max_position_pct / 100)
            available = account.cash - (account.equity * (risk.min_cash_reserve_pct / 100))
            spend = min(max_spend, available)
            qty = spend / state["current_price"]
            qty = round(qty, 2)
            if qty <= 0:
                return {"order_result": None, "execution_status": "skipped"}

        elif action == "sell":
            pos = next((p for p in positions if p.symbol == symbol), None)
            if not pos:
                return {"order_result": None, "execution_status": "skipped"}
            qty = pos.qty

        order = await broker.submit_order(symbol, qty, action, settings.orders.type)
        logger.info(f"{symbol}: order submitted id={order.id} qty={qty} side={action}")
        return {
            "order_result": {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "qty": order.qty,
                "status": order.status,
            },
            "execution_status": "executed",
        }

    except Exception:
        logger.exception(f"{symbol}: order execution failed")
        return {"order_result": None, "execution_status": "failed"}
