# RainierTrader — Technical Design Document

**Version**: 1.0
**Date**: March 8, 2026
**Author**: XUE
**Status**: Draft

---

## 1. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Best financial library ecosystem |
| Agent Framework | LangGraph v1.0 | Industry standard for stateful agent workflows; 47M+ PyPI downloads |
| Broker API | Alpaca Markets | Free paper trading, zero-commission live trading, REST + WebSocket |
| LLM | Claude API (Sonnet) | Best reasoning for financial analysis; user brings own API key |
| Technical Indicators | pandas-ta | Comprehensive indicator library, pandas-native |
| Data Storage | SQLite | Zero-config, single-file database, perfect for local deployment |
| Configuration | YAML + .env | Human-readable config + secure secrets management |
| Scheduling | APScheduler | In-process job scheduling for trading loop |
| CLI | Click or Typer | Clean CLI interface with subcommands |
| OpenClaw Integration | OpenClaw Skill SDK | Thin adapter layer for messaging interface |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RainierTrader                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Entry Points                           │  │
│  │  ┌─────────────┐  ┌──────────────────┐                  │  │
│  │  │  CLI (main)  │  │  OpenClaw Skill   │                  │  │
│  │  │  rainier run │  │  Adapter Layer    │                  │  │
│  │  └──────┬───────┘  └────────┬─────────┘                  │  │
│  └─────────┼───────────────────┼────────────────────────────┘  │
│            │                   │                                │
│            └─────────┬─────────┘                                │
│                      ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LangGraph Trading Workflow                    │  │
│  │                                                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │  │
│  │  │  Market   │→│ Analysis │→│ Decision │→│  Risk   │ │  │
│  │  │  Data     │  │  Engine  │  │  Engine  │  │ Manager │ │  │
│  │  │  Node     │  │  Node    │  │  Node    │  │  Node   │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────┬────┘ │  │
│  │                                                   │      │  │
│  │                                    ┌──────────────▼────┐ │  │
│  │                                    │  Pass / Reject    │ │  │
│  │                                    └───┬──────────┬────┘ │  │
│  │                                        │          │      │  │
│  │                                   ┌────▼───┐  ┌───▼───┐ │  │
│  │                                   │Execute │  │ Log & │ │  │
│  │                                   │ Order  │  │ Skip  │ │  │
│  │                                   │ Node   │  │ Node  │ │  │
│  │                                   └────┬───┘  └───┬───┘ │  │
│  │                                        │          │      │  │
│  │                                        └────┬─────┘      │  │
│  │                                             ▼            │  │
│  │                                      ┌────────────┐      │  │
│  │                                      │  Logger    │      │  │
│  │                                      │  Node      │      │  │
│  │                                      └────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Infrastructure                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │  │
│  │  │ Alpaca   │  │ Claude   │  │ SQLite   │  │ Config  │ │  │
│  │  │ Client   │  │ Client   │  │ Store    │  │ Manager │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Design Principles

1. **Dual Entry Point**: Core logic is entry-point agnostic. CLI and OpenClaw Skill are thin wrappers.
2. **Separation of Concerns**: Each LangGraph node has a single responsibility.
3. **Broker Abstraction**: Alpaca is accessed through an abstract interface, making it swappable.
4. **Config-Driven**: All strategy parameters, risk rules, and watchlists are externalized to YAML.
5. **Fail-Safe**: Every node handles errors gracefully. The agent never places an order it can't explain.

---

## 3. LangGraph Workflow Design

### 3.1 State Definition

```python
from typing import TypedDict, Literal
from dataclasses import dataclass

class TradingState(TypedDict):
    # Input
    symbol: str
    timestamp: str

    # Market Data
    price_data: dict          # OHLCV bars
    current_price: float

    # Analysis
    indicators: dict          # MA, MACD, RSI, BOLL values
    technical_signal: str     # "bullish" | "bearish" | "neutral"

    # Decision
    action: str               # "buy" | "sell" | "hold"
    reasoning: str            # LLM's explanation
    confidence: float         # 0.0 - 1.0

    # Risk Check
    risk_approved: bool
    risk_note: str            # Why rejected if not approved

    # Execution
    order_result: dict | None # Alpaca order response
    execution_status: str     # "executed" | "skipped" | "failed"

    # Logging
    log_entry: dict           # Complete audit record
```

### 3.2 Graph Structure

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(TradingState)

# Add nodes
workflow.add_node("fetch_market_data", fetch_market_data)
workflow.add_node("analyze", analyze_indicators)
workflow.add_node("decide", llm_decision)
workflow.add_node("risk_check", risk_management)
workflow.add_node("execute", execute_order)
workflow.add_node("log_skip", log_skip)
workflow.add_node("log_trade", log_trade)

# Define edges
workflow.set_entry_point("fetch_market_data")
workflow.add_edge("fetch_market_data", "analyze")
workflow.add_edge("analyze", "decide")

# Conditional: hold → skip, buy/sell → risk check
workflow.add_conditional_edges(
    "decide",
    lambda state: "risk_check" if state["action"] != "hold" else "log_skip",
)

# Conditional: risk approved → execute, rejected → skip
workflow.add_conditional_edges(
    "risk_check",
    lambda state: "execute" if state["risk_approved"] else "log_skip",
)

workflow.add_edge("execute", "log_trade")
workflow.add_edge("log_skip", END)
workflow.add_edge("log_trade", END)

app = workflow.compile()
```

### 3.3 Node Specifications

#### Node: fetch_market_data

- **Input**: symbol, timestamp
- **Process**: Call Alpaca Market Data API for latest bars (1min, 5min, 1D)
- **Output**: price_data, current_price
- **Error Handling**: Retry 3x with backoff; if failed, skip this cycle

#### Node: analyze

- **Input**: price_data
- **Process**: Calculate indicators using pandas-ta (SMA 20/50/200, MACD, RSI 14, Bollinger Bands 20)
- **Output**: indicators dict, technical_signal (bullish/bearish/neutral)
- **Error Handling**: If data insufficient for indicator calculation, signal = "neutral"

#### Node: decide (LLM)

- **Input**: indicators, technical_signal, current_price, current portfolio state
- **Process**: Call Claude API with structured prompt including all analysis data
- **Output**: action (buy/sell/hold), reasoning (text), confidence (0-1)
- **Prompt Strategy**: System prompt defines role as conservative trader; user prompt includes all data points
- **Error Handling**: If Claude API fails, default to "hold"

#### Node: risk_check

- **Input**: action, current portfolio, config risk rules
- **Process**: Evaluate against all risk rules
- **Output**: risk_approved (bool), risk_note
- **Rules** (all configurable via YAML):

| Rule | Default | Description |
|------|---------|-------------|
| max_position_pct | 20% | Max % of portfolio in single stock |
| max_positions | 5 | Max number of concurrent positions |
| stop_loss_pct | 3% | Per-trade stop loss |
| daily_loss_limit_pct | 5% | Max daily portfolio drawdown |
| min_cash_reserve_pct | 20% | Minimum cash always held |
| min_confidence | 0.6 | Minimum LLM confidence to act |

#### Node: execute

- **Input**: action, symbol, risk-approved parameters
- **Process**: Calculate position size; submit order to Alpaca Trading API
- **Output**: order_result (Alpaca order response)
- **Order Types**: Market order (default), Limit order (if configured)
- **Error Handling**: If order fails, log error, do not retry automatically

#### Node: log_trade / log_skip

- **Input**: Complete state
- **Process**: Write full audit record to SQLite
- **Output**: log_entry with timestamp, symbol, action, reasoning, execution details

---

## 4. Module Design

### 4.1 Module Dependency Map

```
rainier_trader/
│
├── core/                    # Core trading logic (entry-point agnostic)
│   ├── workflow.py          # LangGraph workflow definition
│   ├── state.py             # TradingState type definition
│   └── orchestrator.py      # Main loop: iterate symbols × schedule
│
├── nodes/                   # LangGraph node implementations
│   ├── market_data.py       # fetch_market_data node
│   ├── analysis.py          # analyze node (technical indicators)
│   ├── decision.py          # decide node (Claude API)
│   ├── risk.py              # risk_check node
│   ├── execution.py         # execute node (Alpaca orders)
│   └── logger.py            # log_trade / log_skip nodes
│
├── clients/                 # External service clients
│   ├── alpaca_client.py     # Alpaca API wrapper (abstract interface)
│   ├── llm_client.py        # Claude API wrapper (abstract interface)
│   └── news_client.py       # News API wrapper (Phase 2)
│
├── models/                  # Data models
│   ├── trade.py             # Trade, Order, Position dataclasses
│   ├── signal.py            # Signal, Indicator dataclasses
│   └── portfolio.py         # Portfolio state model
│
├── storage/                 # Persistence
│   ├── database.py          # SQLite operations
│   └── migrations/          # Schema migrations
│
├── config/                  # Configuration
│   ├── settings.py          # Config loader (YAML + .env)
│   └── defaults.py          # Default values
│
├── adapters/                # Entry point adapters
│   ├── cli.py               # CLI commands (Click/Typer)
│   └── openclaw_skill.py    # OpenClaw Skill adapter
│
└── utils/                   # Shared utilities
    ├── formatting.py         # Output formatting
    └── retry.py              # Retry/backoff logic
```

### 4.2 Key Interfaces

#### Broker Interface (Abstract)

```python
from abc import ABC, abstractmethod

class BrokerClient(ABC):
    @abstractmethod
    async def get_bars(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Fetch OHLCV bars."""

    @abstractmethod
    async def get_account(self) -> Account:
        """Get account info (balance, buying power)."""

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get current positions."""

    @abstractmethod
    async def submit_order(self, symbol: str, qty: float, side: str, type: str) -> Order:
        """Submit a trade order."""

    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        """Get order status."""
```

#### LLM Interface (Abstract)

```python
class LLMClient(ABC):
    @abstractmethod
    async def analyze_and_decide(
        self,
        symbol: str,
        indicators: dict,
        portfolio: Portfolio,
        news: list[str] | None = None,
    ) -> Decision:
        """Analyze market data and return trading decision."""
```

These abstractions allow swapping Alpaca for another broker or Claude for another LLM without touching core logic.

---

## 5. Data Model

### 5.1 SQLite Schema

```sql
-- Trade log: complete audit trail
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,          -- buy, sell, hold
    signal TEXT,                   -- bullish, bearish, neutral
    confidence REAL,
    reasoning TEXT,                -- LLM's explanation
    risk_approved INTEGER,        -- 0 or 1
    risk_note TEXT,
    order_id TEXT,                 -- Alpaca order ID
    quantity REAL,
    price REAL,
    total_value REAL,
    status TEXT,                   -- executed, skipped, failed
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Daily performance summary
CREATE TABLE daily_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    starting_equity REAL,
    ending_equity REAL,
    daily_pnl REAL,
    daily_return_pct REAL,
    trades_executed INTEGER,
    trades_skipped INTEGER,
    win_count INTEGER,
    loss_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Configuration history (for reproducibility)
CREATE TABLE config_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    config_json TEXT NOT NULL,     -- Full YAML config as JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Configuration Design

### 6.1 config.yaml

```yaml
# RainierTrader Configuration

# Trading mode
mode: paper  # paper | live

# Watchlist
watchlist:
  - AAPL
  - MSFT
  - NVDA
  - GOOGL
  - TSLA

# Trading schedule
schedule:
  interval_minutes: 5        # How often to evaluate each symbol
  market_hours_only: true    # Only trade during market hours (9:30-16:00 ET)

# Strategy parameters
strategy:
  indicators:
    sma_fast: 20
    sma_slow: 50
    sma_trend: 200
    rsi_period: 14
    rsi_overbought: 70
    rsi_oversold: 30
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    bb_period: 20
    bb_std: 2
  min_confidence: 0.6        # Minimum LLM confidence to act

# Risk management
risk:
  max_position_pct: 20       # Max % of portfolio per stock
  max_positions: 5           # Max concurrent positions
  stop_loss_pct: 3           # Per-trade stop loss %
  take_profit_pct: 8         # Per-trade take profit % (optional)
  daily_loss_limit_pct: 5    # Stop trading if daily loss exceeds this
  min_cash_reserve_pct: 20   # Always keep this % in cash

# Order settings
orders:
  type: market               # market | limit
  time_in_force: day         # day | gtc

# LLM settings
llm:
  model: claude-sonnet-4-20250514
  temperature: 0.3           # Low temperature for consistent decisions
  max_tokens: 1000

# Notifications (Phase 2)
# notifications:
#   telegram_bot_token: ""
#   telegram_chat_id: ""

# Logging
logging:
  level: INFO                # DEBUG | INFO | WARNING | ERROR
  file: logs/rainier.log
```

### 6.2 .env (Secrets — never committed)

```bash
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ANTHROPIC_API_KEY=your_claude_api_key
```

---

## 7. OpenClaw Skill Design

### 7.1 Skill Manifest

```json
{
  "name": "rainier-trader",
  "version": "1.0.0",
  "description": "Autonomous AI trading agent for U.S. stocks",
  "author": "XUE",
  "commands": [
    {
      "name": "portfolio",
      "description": "Show current portfolio and positions"
    },
    {
      "name": "trades",
      "description": "Show today's trades and decisions"
    },
    {
      "name": "start",
      "description": "Start the trading agent"
    },
    {
      "name": "stop",
      "description": "Stop the trading agent"
    },
    {
      "name": "status",
      "description": "Show agent status (running/stopped, last action)"
    },
    {
      "name": "performance",
      "description": "Show performance summary (daily, weekly, monthly)"
    }
  ],
  "permissions": [
    "network.http",
    "fs.read_config",
    "process.background"
  ]
}
```

### 7.2 Adapter Architecture

```
OpenClaw Gateway
    │
    ▼
┌─────────────────────────┐
│  openclaw_skill.py       │  ← Thin adapter: parses commands, formats responses
│  - parse_command()       │
│  - format_response()     │
│  - start_agent()         │
│  - stop_agent()          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  core/orchestrator.py    │  ← Same core logic as CLI mode
│  (shared with CLI)       │
└─────────────────────────┘
```

The OpenClaw adapter is intentionally thin (~100 lines). It translates OpenClaw commands into calls to the core orchestrator and formats results for messaging output.

---

## 8. Claude API Prompt Design

### 8.1 System Prompt

```
You are RainierTrader, an autonomous stock trading analyst.
Your role is to analyze market data and make trading decisions.

Rules:
1. Be conservative. When in doubt, recommend HOLD.
2. Always provide clear reasoning for your decision.
3. Consider both technical indicators and broader market context.
4. Never chase momentum blindly. Look for confirmation signals.
5. Respect risk management — it's more important than profit.

Output format (JSON):
{
  "action": "buy" | "sell" | "hold",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of your decision"
}
```

### 8.2 User Prompt Template

```
Analyze {symbol} and decide whether to BUY, SELL, or HOLD.

Current Price: ${current_price}
Timestamp: {timestamp}

Technical Indicators:
- SMA(20): {sma_20} | SMA(50): {sma_50} | SMA(200): {sma_200}
- RSI(14): {rsi}
- MACD: {macd} | Signal: {macd_signal} | Histogram: {macd_hist}
- Bollinger Bands: Upper={bb_upper} | Middle={bb_mid} | Lower={bb_lower}

Current Portfolio:
- Cash: ${cash}
- Total Equity: ${equity}
- Current Position in {symbol}: {position_qty} shares @ ${position_avg_price}
- Daily P&L: ${daily_pnl} ({daily_pnl_pct}%)

Respond with JSON only.
```

---

## 9. CLI Design

```bash
# Start the trading agent
rainier run

# Start with specific config
rainier run --config custom-config.yaml

# Check portfolio status
rainier status

# Show today's trades
rainier trades

# Show performance report
rainier report --period week

# Run in paper mode (override config)
rainier run --paper

# Run a single evaluation cycle (for testing)
rainier run-once --symbol AAPL

# Validate configuration
rainier check-config
```

---

## 10. Error Handling Strategy

| Scenario | Behavior |
|----------|----------|
| Alpaca API unreachable | Retry 3x with exponential backoff; if still failing, skip cycle and log warning |
| Claude API unreachable | Default to HOLD; log warning; continue next cycle |
| Claude returns invalid JSON | Parse error → default HOLD; log the raw response for debugging |
| Order rejected by Alpaca | Log full rejection reason; do not retry; alert user |
| Insufficient buying power | Risk manager blocks before order; log as skipped |
| Rate limit hit (Alpaca/Claude) | Respect rate limit headers; pause and retry after cooldown |
| Unexpected crash | State persisted in SQLite; on restart, resume from last known state |
| Config file missing/invalid | Fail fast with clear error message; do not start trading |

---

## 11. Development Plan

### Week 1: Foundation + Data + Core Loop

| Day | Task | Deliverable | Verification |
|-----|------|------------|--------------|
| 1 | Project setup: repo, venv, deps, directory structure, config loader | Skeleton project with `rainier check-config` working | Config loads and validates |
| 2 | Alpaca client: connect, fetch bars, account info, positions | `alpaca_client.py` with tests | Can pull AAPL 5-min bars |
| 3 | Analysis node: pandas-ta indicators | `analysis.py` with tests | Indicators match expected values |
| 4 | Decision node: Claude API integration | `decision.py` with tests | Claude returns valid JSON decision |
| 5 | Execution node: Alpaca paper trading orders | `execution.py` with tests | Can submit and query paper order |
| 6-7 | Wire LangGraph: connect all nodes, test full cycle | `rainier run-once --symbol AAPL` works end-to-end | Full cycle completes with log entry |

### Week 2: Risk + Loop + Polish

| Day | Task | Deliverable | Verification |
|-----|------|------------|--------------|
| 8 | Risk management node: all 6 rules | `risk.py` with tests | Orders correctly blocked by each rule |
| 9 | SQLite logging + daily summary | `database.py` + migrations | Trade history queryable |
| 10 | Orchestrator: multi-symbol loop with scheduler | `orchestrator.py` | Runs on schedule, processes all symbols |
| 11 | CLI: `run`, `status`, `trades`, `report` | Full CLI with Click/Typer | All commands functional |
| 12 | Paper trading test: run full day | Full day test log | No crashes, trades logged correctly |
| 13 | OpenClaw Skill: basic adapter (portfolio, trades, status) | `openclaw_skill.py` + manifest | Commands work via OpenClaw |
| 14 | README, LICENSE, .gitignore, docs, first commit | Complete GitHub-ready repo | New user can clone and run in <10 min |

---

## 12. Testing Strategy

### Unit Tests

- Each node function tested independently with mock data
- Risk rules tested with edge cases (exact limits, overflow, zero balance)
- Config validation tested with valid and invalid YAML

### Integration Tests

- Full LangGraph workflow with mocked API clients
- Alpaca paper trading round-trip (submit order → verify fill)
- Claude API with sample market data → verify valid response

### End-to-End Tests

- Full trading day simulation with paper trading
- Verify: orders placed correctly, risk rules enforced, logs complete
- Manual review of Claude's reasoning quality

### Test Commands

```bash
# Run all tests
pytest tests/

# Run specific module tests
pytest tests/test_risk.py

# Run with coverage
pytest --cov=rainier_trader tests/
```

---

## 13. Repository Structure (GitHub-Ready)

```
rainier-trader/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
│       └── ci.yml              # GitHub Actions: lint + test
├── rainier_trader/
│   ├── __init__.py
│   ├── core/
│   ├── nodes/
│   ├── clients/
│   ├── models/
│   ├── storage/
│   ├── config/
│   ├── adapters/
│   └── utils/
├── tests/
│   ├── test_market_data.py
│   ├── test_analysis.py
│   ├── test_decision.py
│   ├── test_risk.py
│   ├── test_execution.py
│   ├── test_workflow.py
│   └── conftest.py             # Shared fixtures
├── config/
│   ├── config.yaml             # Default config (committed)
│   └── config.example.yaml     # Example with comments
├── docs/
│   ├── quickstart.md
│   ├── configuration.md
│   ├── strategies.md
│   ├── openclaw.md
│   └── architecture.md
├── openclaw/
│   ├── skill.json              # OpenClaw manifest
│   └── README.md               # OpenClaw-specific setup
├── .env.example
├── .gitignore
├── LICENSE                     # MIT
├── README.md
├── pyproject.toml
└── Makefile                    # make install, make test, make run
```

---

## 14. README Outline

```markdown
# 🏔️ RainierTrader

An autonomous AI trading agent for U.S. stocks. Zero human intervention.

Built with LangGraph + Alpaca + Claude API.

## Features
- Fully autonomous: analyzes markets and executes trades automatically
- Local-first: your API keys never leave your machine
- AI-powered: Claude analyzes technicals and news for intelligent decisions
- Risk-managed: configurable stop-loss, position limits, daily loss caps
- OpenClaw compatible: use as a standalone CLI or as an OpenClaw Skill
- Paper & Live: test risk-free, then go live with one config change

## Quick Start (5 minutes)
1. Clone the repo
2. Install dependencies
3. Add your API keys to .env
4. Run: `rainier run --paper`

## Requirements
- Python 3.11+
- Alpaca account (free) — get API keys at alpaca.markets
- Anthropic API key — get at console.anthropic.com
- No GPU required

## Disclaimer
This is a software tool, not financial advice. Trading involves risk.
Past performance does not guarantee future results. Use at your own risk.
```

---

*This document serves as the technical blueprint for implementation. Take it to Claude Code CLI and start building.*
