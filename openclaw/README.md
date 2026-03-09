# RainierTrader — OpenClaw Skill

This directory contains the OpenClaw Skill manifest for RainierTrader.

## Installation

1. Install RainierTrader: `pip install -e .` from the repo root
2. Configure `.env` with your API keys
3. Register the skill with OpenClaw pointing to `openclaw/skill.json`

## Commands

| Command | Description |
|---------|-------------|
| `start` | Start the trading agent in background |
| `stop` | Stop the trading agent |
| `status` | Check if agent is running |
| `portfolio` | Show current positions and equity |
| `trades` | Show today's trade log |
| `performance` | Show P&L summary |

## Example (via OpenClaw chat)

```
You: portfolio
Agent: Equity: $102,341.50 | Cash: $78,200.00 | Daily P&L: +$1,241.50 (+1.23%)
       Positions: AAPL 10 shares @ $170.00 | NVDA 5 shares @ $820.00
```
