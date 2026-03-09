from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Order:
    id: str
    symbol: str
    side: str          # "buy" | "sell"
    qty: float
    type: str          # "market" | "limit"
    status: str
    filled_avg_price: float | None = None
    submitted_at: datetime | None = None


@dataclass
class Position:
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    unrealized_pl: float
    unrealized_plpc: float


@dataclass
class Account:
    equity: float
    cash: float
    buying_power: float
    portfolio_value: float
    daily_pl: float
    daily_pl_pct: float
