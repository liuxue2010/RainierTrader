# RainierTrader — Product Requirements Document (PRD)

**Version**: 1.0
**Date**: March 8, 2026
**Author**: XUE
**Status**: Draft

---

## 1. Executive Summary

RainierTrader is an open-source, autonomous AI trading agent for U.S. stocks. It runs locally on the user's machine, connects to Alpaca for trade execution and Claude API for intelligent decision-making, and requires zero human intervention once configured. The name is inspired by Mount Rainier — symbolizing stability, endurance, and commanding presence.

### Core Value Proposition

**"Set it and forget it."** — RainierTrader handles the last mile of trading: from market analysis to order execution, fully automated, with no human in the loop.

---

## 2. Background & Motivation

### 2.1 Problem Statement

Retail traders spend hours daily watching charts, reading news, and manually executing trades. This is time-consuming, emotionally draining, and error-prone. Existing solutions either require deep technical knowledge (quantitative trading platforms) or charge high fees (managed trading services) while demanding users hand over account credentials.

### 2.2 Opportunity

The convergence of three technologies makes a fully autonomous trading agent feasible for individual investors: LLM APIs (Claude) for intelligent analysis and decision-making, commission-free trading APIs (Alpaca) for programmatic order execution, and AI agent frameworks (LangGraph) for reliable stateful workflow orchestration.

### 2.3 Project Goals

1. **Primary**: Build a fully autonomous trading agent that executes U.S. stock trades without human intervention
2. **Secondary**: Serve as a portfolio project demonstrating AI agent design and engineering expertise
3. **Long-term**: Grow into a product with a sustainable subscription-based business model

---

## 3. User Personas

### 3.1 Persona 1: The Busy Trader (Primary)

- **Profile**: Working professional who actively trades U.S. stocks but lacks time to monitor markets daily
- **Pain Point**: Cannot watch charts during work hours; misses trading opportunities; makes emotional decisions
- **Need**: A reliable agent that trades on their behalf following defined strategies
- **Technical Skill**: Can follow installation instructions, comfortable with terminal/CLI basics

### 3.2 Persona 2: The Tech-Savvy Investor (Secondary)

- **Profile**: Developer or engineer interested in algorithmic trading
- **Pain Point**: Wants to automate trading strategies but doesn't want to build infrastructure from scratch
- **Need**: A well-architected, extensible codebase they can customize and extend
- **Technical Skill**: Can read and modify Python code, understands APIs

### 3.3 Persona 3: The OpenClaw User (Future)

- **Profile**: Already uses OpenClaw as their personal AI agent
- **Pain Point**: Wants to add trading capability to their existing agent setup
- **Need**: A plug-and-play OpenClaw Skill for autonomous trading
- **Technical Skill**: Familiar with OpenClaw skill installation

---

## 4. Use Cases

### UC-1: Fully Autonomous Daily Trading

The user configures RainierTrader with their watchlist, strategy parameters, and risk limits. The agent runs continuously during market hours, analyzes market conditions, and executes buy/sell orders automatically. The user reviews a daily summary of all trades and portfolio performance.

### UC-2: Paper Trading Validation

Before risking real money, the user runs RainierTrader against Alpaca's paper trading environment. The agent operates identically to live mode but with simulated funds. The user evaluates strategy performance over weeks before switching to live trading.

### UC-3: OpenClaw Integration

An OpenClaw user installs RainierTrader as a Skill. They can ask their OpenClaw agent via WhatsApp/Telegram: "How's my portfolio doing?" or "What trades did you make today?" The trading agent runs in the background and reports through OpenClaw's messaging interface.

---

## 5. Functional Requirements

### 5.1 MVP (Phase 1 — Weeks 1-2)

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| F-01 | Market Data Retrieval | P0 | Fetch real-time and historical price data via Alpaca API |
| F-02 | Technical Analysis | P0 | Calculate indicators: MA, EMA, MACD, RSI, Bollinger Bands |
| F-03 | LLM Decision Engine | P0 | Claude API analyzes technicals + generates buy/sell/hold signals |
| F-04 | Risk Management | P0 | Per-trade stop-loss, daily loss limit, max position size, cash reserve |
| F-05 | Order Execution | P0 | Execute market/limit orders via Alpaca Trading API |
| F-06 | Portfolio Tracking | P0 | Query account balance, positions, and P&L |
| F-07 | Trade Logging | P0 | Record all decisions, reasoning, and execution results in SQLite |
| F-08 | Configuration | P0 | YAML config for watchlist, strategy params, risk rules, API keys |
| F-09 | CLI Interface | P0 | Command-line interface to start, stop, and monitor the agent |
| F-10 | Paper/Live Switch | P0 | Single config flag to switch between paper and live trading |

### 5.2 Phase 2 — Enhanced Intelligence (Weeks 3-6)

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| F-11 | News Sentiment Analysis | P1 | Fetch financial news, use Claude to extract sentiment signals |
| F-12 | Multi-Signal Decision | P1 | Combine technicals + sentiment + news for holistic decisions |
| F-13 | Stock Screening | P1 | Auto-discover stocks meeting criteria (volume, volatility, sector) |
| F-14 | Notifications | P1 | Push trade alerts via Telegram/Discord/Email |
| F-15 | Strategy Backtesting | P1 | Test strategies against historical data with performance metrics |
| F-16 | Performance Dashboard | P2 | Web UI showing portfolio, equity curve, trade history |

### 5.3 Phase 3 — Platform & Distribution (Months 2-6)

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| F-17 | OpenClaw Skill | P1 | Package as OpenClaw Skill with messaging interface |
| F-18 | Multi-Account | P2 | Support multiple Alpaca accounts in single instance |
| F-19 | Strategy Marketplace | P2 | Users can share and import trading strategies |
| F-20 | Pro Features | P2 | License-gated advanced strategies and analytics |

---

## 6. Non-Functional Requirements

### 6.1 Security

- API keys stored in local .env file, never committed to Git
- No user credentials transmitted to any third-party server
- All trading operations happen directly between user's machine and Alpaca
- Claude API calls contain only market data and analysis, never account credentials

### 6.2 Reliability

- Graceful error handling for API failures (network, rate limits, Alpaca downtime)
- Automatic retry with exponential backoff
- Agent state persisted to disk; recoverable after crash/restart
- All trades logged with full audit trail

### 6.3 Performance

- Trading loop cycle: under 30 seconds per evaluation
- Minimal resource usage: runs on any machine with Python 3.11+ and internet
- No GPU required

### 6.4 Usability

- Setup in under 10 minutes: clone, install deps, add API keys, run
- Clear, concise documentation with quick-start guide
- Sensible defaults for all configuration parameters
- Meaningful error messages and troubleshooting guide

---

## 7. Business Model

### 7.1 Growth Path

```
Phase 1: Self-use → Validate strategy, build core product
Phase 2: Friends & Community → Free open-source, gather feedback, build GitHub stars
Phase 3: Monetization → Open Core model with paid Pro features
Phase 4: Scale → Optional SaaS version with OAuth (if demand warrants)
```

### 7.2 Open Core Model

**Free (Open Source)**:
- Core trading agent with basic strategies
- Paper trading and live trading
- Basic risk management
- CLI interface
- OpenClaw Skill (basic)
- Community support via GitHub Issues

**Pro (Paid Subscription)**:
- Advanced LLM strategies (multi-factor, adaptive)
- Advanced backtesting with detailed analytics
- Multi-account management
- Priority notifications with custom alerts
- Premium OpenClaw Skill features
- Email support

### 7.3 Pricing (Tentative)

- **Free**: $0/month — Core features, community support
- **Pro**: $29-49/month — Advanced features, email support
- **Enterprise**: Custom — Multi-account, custom strategies, dedicated support

### 7.4 Compliance Notes

- Local deployment model: user runs software on their own machine with their own API keys
- RainierTrader is a software tool, not a financial advisor
- No custody of user funds or credentials
- Clear disclaimers: not financial advice, past performance doesn't guarantee future results
- SEC/FINRA RIA registration likely NOT required for tool-only model (consult lawyer before scaling)

---

## 8. Competitive Landscape

| Project | Stars | Differentiator | RainierTrader Advantage |
|---------|-------|---------------|------------------------|
| virattt/ai-hedge-fund | 43k+ | Multi-agent decision, no execution | We execute trades (last mile) |
| TradingAgents | ~5k | Research framework, no live trading | Full pipeline: analysis → execution |
| AlpacaTradingAgent | ~1k | Alpaca integration, Gradio UI | Cleaner architecture, OpenClaw integration |
| AI-Trader | ~3k | Multi-market benchmark | Production-ready for real users |

**RainierTrader's unique position**: The only open-source trading agent that goes from analysis to execution with zero human intervention, runs locally for maximum trust, and integrates with OpenClaw for messaging-based interaction.

---

## 9. Success Metrics

### MVP (Month 1)

- Agent runs continuously for 5 trading days without crashes
- Executes at least 10 paper trades with correct risk management
- Setup documented and reproducible by a non-author developer

### Growth (Months 2-6)

- 500+ GitHub stars
- 10+ community contributors
- 50+ active users (paper + live)
- OpenClaw Skill published and functional

### Monetization (Months 6-12)

- 100+ Pro subscribers
- Positive net revenue after API costs
- NPS score > 40 from Pro users

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Strategy loses money | High | High | Strong risk management defaults; extensive paper trading period; clear disclaimers |
| Alpaca API changes/downtime | Medium | High | Abstract broker interface; easy to swap providers |
| Claude API cost spikes | Medium | Medium | Configurable call frequency; caching; future local model support |
| Regulatory concerns | Low | High | Local-only deployment; no custody; legal disclaimers; consult lawyer at scale |
| OpenClaw architecture changes | Medium | Low | Thin adapter layer; core logic independent of OpenClaw |
| Security breach (API keys leaked) | Low | High | .env file in .gitignore; documentation on key management; no cloud storage |

---

## 11. Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| MVP | Weeks 1-2 | Core agent, paper trading, CLI, basic strategies, documentation |
| Enhanced | Weeks 3-6 | News analysis, backtesting, notifications, improved strategies |
| OpenClaw | Weeks 7-8 | OpenClaw Skill adapter, messaging interface |
| Pro | Months 3-6 | Pro features, license system, marketing site |

---

*This document is a living artifact and will be updated as the project evolves.*
