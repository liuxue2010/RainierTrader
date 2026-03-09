from dataclasses import dataclass, field
from rainier_trader.models.trade import Account, Position


@dataclass
class Portfolio:
    account: Account
    positions: list[Position] = field(default_factory=list)

    def get_position(self, symbol: str) -> Position | None:
        return next((p for p in self.positions if p.symbol == symbol), None)

    def position_value(self, symbol: str) -> float:
        pos = self.get_position(symbol)
        return pos.qty * pos.current_price if pos else 0.0

    def position_pct(self, symbol: str) -> float:
        if self.account.equity == 0:
            return 0.0
        return (self.position_value(symbol) / self.account.equity) * 100
