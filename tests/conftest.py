import pytest
from unittest.mock import AsyncMock, MagicMock

from rainier_trader.models.trade import Account, Position, Order
from rainier_trader.models.portfolio import Portfolio


@pytest.fixture
def mock_account():
    return Account(
        equity=100_000.0,
        cash=80_000.0,
        buying_power=80_000.0,
        portfolio_value=100_000.0,
        daily_pl=500.0,
        daily_pl_pct=0.5,
    )


@pytest.fixture
def mock_position():
    return Position(
        symbol="AAPL",
        qty=10.0,
        avg_entry_price=170.0,
        current_price=175.0,
        unrealized_pl=50.0,
        unrealized_plpc=0.029,
    )


@pytest.fixture
def mock_portfolio(mock_account, mock_position):
    return Portfolio(account=mock_account, positions=[mock_position])


@pytest.fixture
def mock_broker(mock_account, mock_position):
    broker = AsyncMock()
    broker.get_account.return_value = mock_account
    broker.get_positions.return_value = [mock_position]
    broker.submit_order.return_value = Order(
        id="order-123",
        symbol="AAPL",
        side="buy",
        qty=10.0,
        type="market",
        status="accepted",
    )
    return broker


@pytest.fixture
def sample_state():
    return {
        "symbol": "AAPL",
        "timestamp": "2026-03-08T10:00:00-05:00",
        "price_data": {},
        "current_price": 175.0,
        "indicators": {
            "current_price": 175.0,
            "sma_20": 172.0,
            "sma_50": 168.0,
            "sma_200": 155.0,
            "rsi": 45.0,
            "macd": 1.2,
            "macd_signal": 0.8,
            "macd_hist": 0.4,
            "bb_upper": 180.0,
            "bb_mid": 172.0,
            "bb_lower": 164.0,
        },
        "technical_signal": "bullish",
        "action": "buy",
        "reasoning": "Bullish momentum confirmed",
        "confidence": 0.75,
        "risk_approved": False,
        "risk_note": "",
        "order_result": None,
        "execution_status": "skipped",
        "log_entry": {},
    }
