from abc import ABC, abstractmethod

import pandas as pd

from rainier_trader.models.trade import Account, Order, Position


class BrokerClient(ABC):
    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Fetch OHLCV bars."""

    @abstractmethod
    def get_account(self) -> Account:
        """Get account info."""

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """Get current positions."""

    @abstractmethod
    def submit_order(self, symbol: str, qty: float, side: str, order_type: str) -> Order:
        """Submit a trade order."""

    @abstractmethod
    def get_order(self, order_id: str) -> Order:
        """Get order status."""


class AlpacaClient(BrokerClient):
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        from alpaca.trading.client import TradingClient
        from alpaca.data.historical import StockHistoricalDataClient

        self.trading = TradingClient(api_key, secret_key, paper=paper)
        self.data = StockHistoricalDataClient(api_key, secret_key)

    def get_bars(self, symbol: str, timeframe: str = "5Min", limit: int = 200) -> pd.DataFrame:
        from datetime import datetime, timedelta, timezone
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        tf_map = {
            "1Min": (TimeFrame(1, TimeFrameUnit.Minute), timedelta(days=5)),
            "5Min": (TimeFrame(5, TimeFrameUnit.Minute), timedelta(days=10)),
            "1D": (TimeFrame(1, TimeFrameUnit.Day), timedelta(days=365)),
        }
        tf, lookback = tf_map[timeframe]
        now = datetime.now(timezone.utc)
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=now - lookback,
            end=now,
            limit=limit,
            feed="iex",
        )
        bars = self.data.get_stock_bars(request)
        df = bars.df

        if df.empty:
            return df

        # Alpaca returns MultiIndex (symbol, timestamp) — flatten to just timestamp
        if isinstance(df.index, pd.MultiIndex):
            df = df.droplevel(0)

        df.index = pd.to_datetime(df.index)
        return df

    def get_account(self) -> Account:
        acct = self.trading.get_account()
        equity = float(acct.equity)
        last_equity = float(acct.last_equity)
        daily_pl = equity - last_equity
        daily_pl_pct = (daily_pl / last_equity * 100) if last_equity else 0.0
        return Account(
            equity=equity,
            cash=float(acct.cash),
            buying_power=float(acct.buying_power),
            portfolio_value=float(acct.portfolio_value),
            daily_pl=daily_pl,
            daily_pl_pct=daily_pl_pct,
        )

    def get_positions(self) -> list[Position]:
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

    def submit_order(self, symbol: str, qty: float, side: str, order_type: str = "market") -> Order:
        from alpaca.trading.requests import MarketOrderRequest
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

    def get_order(self, order_id: str) -> Order:
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
