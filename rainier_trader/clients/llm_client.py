from abc import ABC, abstractmethod

import anthropic

from rainier_trader.models.portfolio import Portfolio
from rainier_trader.models.signal import Decision

SYSTEM_PROMPT = """\
You are RainierTrader, an autonomous stock trading analyst.
Your role is to analyze market data and make trading decisions.

Rules:
1. Be conservative. When in doubt, recommend HOLD.
2. Always provide clear reasoning for your decision.
3. Consider both technical indicators and broader market context.
4. Never chase momentum blindly. Look for confirmation signals.
5. Respect risk management — it's more important than profit.

Output format (JSON only, no other text):
{
  "action": "buy" | "sell" | "hold",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of your decision"
}
"""

USER_PROMPT_TEMPLATE = """\
Analyze {symbol} and decide whether to BUY, SELL, or HOLD.

Current Price: ${current_price:.2f}
Timestamp: {timestamp}

Technical Indicators:
- SMA(20): {sma_20} | SMA(50): {sma_50} | SMA(200): {sma_200}
- RSI(14): {rsi}
- MACD: {macd} | Signal: {macd_signal} | Histogram: {macd_hist}
- Bollinger Bands: Upper={bb_upper} | Middle={bb_mid} | Lower={bb_lower}

Current Portfolio:
- Cash: ${cash:.2f}
- Total Equity: ${equity:.2f}
- Current Position in {symbol}: {position_qty} shares @ ${position_avg_price}
- Daily P&L: ${daily_pnl:.2f} ({daily_pnl_pct:.2f}%)

Respond with JSON only.
"""


class LLMClient(ABC):
    @abstractmethod
    def analyze_and_decide(
        self,
        symbol: str,
        indicators: dict,
        portfolio: Portfolio,
        timestamp: str,
        news: list[str] | None = None,
    ) -> Decision:
        """Analyze market data and return trading decision."""


class ClaudeClient(LLMClient):
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def analyze_and_decide(
        self,
        symbol: str,
        indicators: dict,
        portfolio: Portfolio,
        timestamp: str,
        news: list[str] | None = None,
    ) -> Decision:
        import json

        pos = portfolio.get_position(symbol)
        prompt = USER_PROMPT_TEMPLATE.format(
            symbol=symbol,
            current_price=indicators.get("current_price", 0),
            timestamp=timestamp,
            sma_20=_fmt(indicators.get("sma_20")),
            sma_50=_fmt(indicators.get("sma_50")),
            sma_200=_fmt(indicators.get("sma_200")),
            rsi=_fmt(indicators.get("rsi")),
            macd=_fmt(indicators.get("macd")),
            macd_signal=_fmt(indicators.get("macd_signal")),
            macd_hist=_fmt(indicators.get("macd_hist")),
            bb_upper=_fmt(indicators.get("bb_upper")),
            bb_mid=_fmt(indicators.get("bb_mid")),
            bb_lower=_fmt(indicators.get("bb_lower")),
            cash=portfolio.account.cash,
            equity=portfolio.account.equity,
            position_qty=pos.qty if pos else 0,
            position_avg_price=f"{pos.avg_entry_price:.2f}" if pos else "N/A",
            daily_pnl=portfolio.account.daily_pl,
            daily_pnl_pct=portfolio.account.daily_pl_pct,
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code blocks if Claude wraps the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            data = json.loads(raw)
            return Decision(
                action=data["action"],
                confidence=float(data["confidence"]),
                reasoning=data["reasoning"],
            )
        except (json.JSONDecodeError, KeyError):
            return Decision(action="hold", confidence=0.0, reasoning=f"Parse error: {raw[:200]}")


def _fmt(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "N/A"
