from abc import ABC, abstractmethod

import pandas as pd

from rainier_trader.models.trade import Account, Order, Position


class BrokerClient(ABC):
    @abstractmethod
    async def get_bars(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Fetch OHLCV bars."""

    @abstractmethod
    async def get_account(self) -> Account:
        """Get account info."""

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get current positions."""

    @abstractmethod
    async def submit_order(self, symbol: str, qty: float, side: str, order_type: str) -> Order:
        """Submit a trade order."""

    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        """Get order status."""


class AlpacaClient(BrokerClient):
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        from alpaca.trading.client import TradingClient
        from alpaca.data.historical import StockHistoricalDataClient

        self.trading = TradingClient(api_key, secret_key, paper=paper)
        self.data = StockHistoricalDataClient(api_key, secret_key)

    async def get_bars(self, symbol: str, timeframe: str = "5Min", limit: int = 200) -> pd.DataFrame:
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        tf_map = {
            "1Min": TimeFrame(1, TimeFrameUnit.Minute),
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "1D": TimeFrame(1, TimeFrameUnit.Day),
        }
        request = StockBarsRequest(symbol_or_symbols=symbol, timeframe=tf_map[timeframe], limit=limit)
        bars = self.data.get_stock_bars(request)
        return bars.df

    async def get_account(self) -> Account:
        acct = self.trading.get_account()
        daily_pl = float(acct.equity) - float(acct.last_equity)
        daily_pl_pct = (daily_pl / float(acct.last_equity) * 100) if float(acct.last_equity) else 0.0
        return Account(
            equity=float(acct.equity),
            cash=float(acct.cash),
            buying_power=float(acct.buying_power),
            portfolio_value=float(acct.portfolio_value),
            daily_pl=daily_pl,
            daily_pl_pct=daily_pl_pct,
        )

    async def get_positions(self) -> list[Position]:
        positions = self.trading.get_all_positions()
        return [
            Position(
                symbol=p.symbol,
                qty=float(p.qty),
                avg_entry_price=float(p.avg_entry_price),
                current_price=float(p.current_price),
                unrealized_pl=float(p.unrealized_pl),
                unrealized_plpc=float(p.unrealized_plpc),
            )
            for p in positions
        ]

    async def submit_order(self, symbol: str, qty: float, side: str, order_type: str = "market") -> Order:
        from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
        request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY,
        )
        result = self.trading.submit_order(request)
        return Order(
            id=str(result.id),
            symbol=result.symbol,
            side=side,
            qty=float(result.qty),
            type=order_type,
            status=str(result.status),
            submitted_at=result.submitted_at,
        )

    async def get_order(self, order_id: str) -> Order:
        result = self.trading.get_order_by_id(order_id)
        return Order(
            id=str(result.id),
            symbol=result.symbol,
            side=str(result.side),
            qty=float(result.qty),
            type=str(result.order_type),
            status=str(result.status),
            filled_avg_price=float(result.filled_avg_price) if result.filled_avg_price else None,
        )
