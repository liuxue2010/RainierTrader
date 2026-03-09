# RainierTrader

An autonomous AI trading agent for U.S. stocks. Zero human intervention.

Built with **LangGraph** + **Alpaca** + **Claude API**.

> Named after Mount Rainier — symbolizing stability, endurance, and commanding presence.

## Features

- **Fully autonomous** — analyzes markets and executes trades automatically
- **Local-first** — your API keys never leave your machine
- **AI-powered** — Claude analyzes technicals for intelligent buy/sell/hold decisions
- **Risk-managed** — configurable stop-loss, position limits, daily loss caps
- **Paper & Live** — test risk-free, then go live with one config change
- **OpenClaw compatible** — use as CLI or as an OpenClaw Skill

## Quick Start

```bash
# 1. Clone
git clone https://github.com/liuxue2010/RainierTrader.git
cd RainierTrader

# 2. Install
pip install -e ".[dev]"

# 3. Configure secrets
cp .env.example .env
# Edit .env with your Alpaca and Anthropic API keys

# 4. Validate config
rainier check-config

# 5. Run in paper mode
rainier run --paper
```

## Requirements

- Python 3.11+
- [Alpaca account](https://alpaca.markets) (free) — for paper and live trading
- [Anthropic API key](https://console.anthropic.com) — for Claude decision-making
- No GPU required

## CLI Commands

```bash
rainier run              # Start the trading agent
rainier run --paper      # Run in paper trading mode
rainier run-once AAPL    # Single evaluation cycle for a symbol
rainier status           # Show agent status and last action
rainier trades           # Show today's trades
rainier report --period week  # Performance report
rainier check-config     # Validate configuration
```

## Configuration

Edit `config/config.yaml` to set your watchlist, strategy parameters, and risk rules.
All risk parameters have sensible defaults — no tuning required to get started.

See [docs/configuration.md](docs/configuration.md) for full reference.

## Architecture

```
CLI / OpenClaw Skill
        │
        ▼
LangGraph Workflow
  fetch_market_data → analyze → decide (Claude) → risk_check → execute → log
        │
        ▼
Infrastructure: Alpaca Client | Claude Client | SQLite | Config
```

See [docs/architecture.md](docs/architecture.md) for details.

## Disclaimer

This is a software tool, not financial advice. Trading involves significant risk of loss.
Past performance does not guarantee future results. Use at your own risk.
