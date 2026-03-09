import logging

from rainier_trader.core.state import TradingState
from rainier_trader.utils.retry import retry_async

logger = logging.getLogger(__name__)


async def fetch_market_data(state: TradingState) -> dict:
    from rainier_trader.clients.alpaca_client import AlpacaClient
    from rainier_trader.config.settings import load_settings

    settings = load_settings()
    client = AlpacaClient(
        settings.alpaca_api_key,
        settings.alpaca_secret_key,
        paper=settings.is_paper,
    )

    symbol = state["symbol"]
    try:
        bars = await retry_async(client.get_bars, symbol, "5Min", 250)
        current_price = float(bars["close"].iloc[-1])
        logger.info(f"{symbol}: fetched {len(bars)} bars, price=${current_price:.2f}")
        return {"price_data": bars.to_dict(), "current_price": current_price}
    except Exception:
        logger.exception(f"{symbol}: failed to fetch market data")
        raise
