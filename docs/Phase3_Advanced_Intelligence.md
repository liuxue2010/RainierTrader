# RainierTrader — Phase 3: Advanced Intelligence

**Version**: 1.0
**Date**: March 8, 2026
**Author**: XUE
**Status**: Draft

---

## Overview

Phase 3 extends Claude's decision-making context beyond technical indicators and news sentiment (Phase 2) to include fundamental data, macroeconomic signals, quantitative models, and market microstructure data. The goal is to make RainierTrader competitive with professional-grade trading systems while remaining locally deployable.

---

## 1. Data Sources to Add

### 1.1 Earnings Reports

**What**: Quarterly earnings results (EPS actual vs estimate, revenue, guidance)

**Why it matters**: Stocks commonly move 5–20% on earnings day. Knowing whether earnings are upcoming or just released is critical context for any buy/sell decision.

**Implementation**:
- **Source**: [Alpaca Corporate Actions API](https://docs.alpaca.markets) or [Financial Modeling Prep API](https://financialmodelingprep.com) (free tier available)
- **What to feed Claude**:
  ```
  Upcoming Earnings: AAPL reports in 3 days (March 11)
  Last Earnings: EPS $2.40 vs $2.31 estimate (+3.9% beat)
  Revenue: $124.3B vs $122.0B estimate (+1.9% beat)
  YoY Revenue Growth: +4.2%
  ```
- **New node**: `nodes/earnings.py` — fetches and formats earnings data per symbol
- **Risk rule**: block buy orders within 2 days of earnings (configurable)

---

### 1.2 SEC Filings

**What**: 10-K (annual), 10-Q (quarterly), 8-K (material events), insider trading (Form 4)

**Why it matters**: Insider buying is a strong bullish signal. 8-K filings reveal material events (acquisitions, CEO changes, lawsuits) that technicals won't capture.

**Implementation**:
- **Source**: [SEC EDGAR API](https://efts.sec.gov/LATEST/search-index) (free, no key required)
- **What to feed Claude**:
  ```
  Recent SEC Filings (last 30 days):
  - Form 4 (Insider Buy): CEO Tim Cook bought 10,000 shares @ $255.00 on Mar 1
  - 8-K filed Mar 5: New $100B share buyback program announced
  ```
- **New client**: `clients/sec_client.py`
- **Focus**: Form 4 (insider trades) and 8-K (material events) — highest signal-to-noise ratio

---

### 1.3 Macroeconomic Data

**What**: Federal Reserve interest rates, CPI (inflation), unemployment, GDP growth, yield curve

**Why it matters**: Macro conditions set the backdrop for all stock movements. Rising rates hurt growth stocks; high inflation signals Fed tightening; inverted yield curve predicts recession.

**Implementation**:
- **Source**: [FRED API](https://fred.stlouisfed.org/docs/api/fred/) (Federal Reserve, free)
- **What to feed Claude**:
  ```
  Macro Context:
  - Fed Funds Rate: 4.50% (last change: -0.25% on Jan 29)
  - CPI YoY: 2.8% (target: 2.0%)
  - 10Y-2Y Yield Spread: +0.32% (normal, not inverted)
  - Unemployment: 4.1%
  - Next FOMC Meeting: March 19 (market expects hold)
  ```
- **New client**: `clients/macro_client.py`
- **Caching**: Macro data changes slowly — cache with 1-day TTL to avoid redundant API calls

---

### 1.4 Options Flow / Short Interest

**What**: Unusual options activity (large call/put buys), short interest ratio, days-to-cover

**Why it matters**: Large institutional options bets often predict near-term price direction. High short interest can lead to short squeezes. Smart money leaves footprints in options markets.

**Implementation**:
- **Source**: [Unusual Whales API](https://unusualwhales.com/api) or [Tradier API](https://developer.tradier.com) for options data
- **Short interest**: [FINRA short sale data](https://www.finra.org/investors/learn-to-invest/advanced-investing/short-selling) (free, delayed)
- **What to feed Claude**:
  ```
  Options Flow (last 24h):
  - Unusual call sweep: 5,000 contracts Mar 21 $270C @ $2.40 (bullish, $1.2M premium)
  - Put/Call Ratio: 0.72 (below 1.0 = bullish sentiment)

  Short Interest:
  - Short Float: 0.8% (low — low squeeze risk)
  - Days to Cover: 1.2
  ```
- **New client**: `clients/options_client.py`

---

### 1.5 Quantitative Models

**What**: Rule-based signals derived from price/volume data, independent of LLM reasoning

**Why it matters**: LLMs can be inconsistent. Quantitative signals provide deterministic, backtestable rules that complement Claude's qualitative reasoning.

**Models to implement**:

| Model | Signal | Logic |
|-------|--------|-------|
| Mean Reversion | Buy oversold, sell overbought | Z-score of price vs 20-day mean > 2σ |
| Momentum | Follow strong trends | 12-1 month return positive + volume confirmation |
| Golden/Death Cross | Trend change | SMA(50) crosses SMA(200) |
| Volume Spike | Unusual activity | Volume > 2x 20-day average |
| Gap Detection | Opening gap trades | Price gaps up/down > 2% from prior close |

**Implementation**:
- **New module**: `nodes/quant_signals.py`
- **Output**: Add `quant_signals` dict to `TradingState`
- **Feed to Claude**:
  ```
  Quantitative Signals:
  - Mean Reversion: NEUTRAL (z-score: +0.8)
  - Momentum (12-1M): BULLISH (+18.4% return)
  - Golden Cross: ACTIVE (SMA50 crossed above SMA200 on Feb 12)
  - Volume: NORMAL (0.9x 20-day average)
  ```

---

## 2. Updated TradingState

```python
class TradingState(TypedDict):
    # ... existing fields ...

    # Phase 3 additions
    earnings: dict | None       # upcoming/recent earnings data
    sec_filings: list[dict]     # recent 8-K and Form 4 filings
    macro: dict | None          # macroeconomic indicators
    options_flow: dict | None   # unusual options activity + short interest
    quant_signals: dict         # quantitative model outputs
```

---

## 3. Updated Claude Prompt

The user prompt grows to include all new data:

```
Analyze {symbol} and decide whether to BUY, SELL, or HOLD.

[... existing technical indicators ...]

Earnings:
- Next report: March 11 (in 3 days) — CAUTION: avoid buying before earnings
- Last quarter: EPS beat +3.9%, Revenue beat +1.9%

Recent SEC Filings:
- Insider Buy: CEO bought 10,000 shares @ $255 on Mar 1 (bullish signal)
- 8-K Mar 5: $100B buyback announced

Macroeconomic Context:
- Fed Rate: 4.50% | CPI: 2.8% | Yield Spread: +0.32% (healthy)
- Next FOMC: March 19 (hold expected)

Options Flow:
- Unusual bullish call sweep detected ($1.2M premium, Mar 21 $270C)
- Put/Call Ratio: 0.72 (bullish sentiment)

Quantitative Signals:
- Momentum: BULLISH | Golden Cross: ACTIVE | Volume: NORMAL

Respond with JSON only.
```

---

## 4. New Nodes in the Workflow

```
fetch_market_data
      ↓
fetch_fundamentals  ← NEW (earnings + SEC + macro + options, runs in parallel)
      ↓
analyze_indicators
      ↓
quant_signals       ← NEW
      ↓
decide (Claude)     ← now sees everything
      ↓
risk_check
      ↓
execute
      ↓
log_trade
```

---

## 5. New Risk Rules

| Rule | Default | Description |
|------|---------|-------------|
| `block_before_earnings_days` | 2 | Block buys within N days of earnings |
| `require_quant_confirmation` | false | Only act if quant signals agree with Claude |
| `macro_rate_threshold` | 5.5% | Reduce position sizes if Fed rate exceeds this |

---

## 6. Data Sources Summary

| Data | Source | Cost | Update Frequency |
|------|--------|------|-----------------|
| Earnings | Financial Modeling Prep | Free tier (250 req/day) | Quarterly |
| SEC Filings | SEC EDGAR | Free | Real-time |
| Macro (Fed, CPI) | FRED API | Free | Monthly/quarterly |
| Options Flow | Unusual Whales / Tradier | Paid ($30-50/mo) | Real-time |
| Short Interest | FINRA | Free | Bi-weekly |
| Quant Signals | Computed locally | Free | Per cycle |

---

## 7. Implementation Order

1. **Quant signals** — no new API, highest ROI, pure computation
2. **Earnings** — free API, high impact, straightforward integration
3. **SEC filings** — free EDGAR API, insider trades are valuable signal
4. **Macro data** — free FRED API, good context for long-term decisions
5. **Options flow** — paid API, highest alpha but least essential for MVP

---

*This document extends the Phase 2 roadmap. Implement after news sentiment (F-11, F-12) is stable.*
