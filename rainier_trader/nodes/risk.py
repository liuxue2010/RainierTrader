import logging

from rainier_trader.core.state import TradingState

logger = logging.getLogger(__name__)


def risk_check(state: TradingState) -> dict:
    from rainier_trader.clients.alpaca_client import AlpacaClient
    from rainier_trader.config.settings import load_settings
    from rainier_trader.models.portfolio import Portfolio

    settings = load_settings()
    risk = settings.risk
    broker = AlpacaClient(settings.alpaca_api_key, settings.alpaca_secret_key, paper=settings.is_paper)

    account = broker.get_account()
    positions = broker.get_positions()
    portfolio = Portfolio(account=account, positions=positions)

    symbol = state["symbol"]
    action = state["action"]
    confidence = state["confidence"]

    if confidence < settings.strategy.min_confidence:
        return _reject(f"Confidence {confidence:.2f} below threshold {settings.strategy.min_confidence}")

    if account.daily_pl_pct <= -risk.daily_loss_limit_pct:
        return _reject(f"Daily loss limit hit ({account.daily_pl_pct:.2f}%)")

    if action == "buy":
        if len(positions) >= risk.max_positions:
            return _reject(f"Max positions ({risk.max_positions}) already held")

        min_cash = account.equity * (risk.min_cash_reserve_pct / 100)
        if account.cash <= min_cash:
            return _reject(f"Insufficient cash — reserve floor ${min_cash:.2f} would be breached")

        pos_pct = portfolio.position_pct(symbol)
        if pos_pct >= risk.max_position_pct:
            return _reject(f"Already at max position size ({pos_pct:.1f}%)")

    if action == "sell":
        pos = portfolio.get_position(symbol)
        if pos is None or pos.qty <= 0:
            return _reject(f"No position in {symbol} to sell")

    logger.info(f"{symbol}: risk check PASSED for {action}")
    return {"risk_approved": True, "risk_note": ""}


def _reject(reason: str) -> dict:
    logger.info(f"Risk check REJECTED: {reason}")
    return {"risk_approved": False, "risk_note": reason}
