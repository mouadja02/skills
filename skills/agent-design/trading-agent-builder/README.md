# Trading Agent Builder

Build multi-agent AI trading systems that combine LLM reasoning with quantitative analysis. Covers the full pipeline: market data ingestion, multi-agent analysis (fundamentals, technicals, sentiment, risk), signal generation, backtesting, and paper trading.

> ⚠️ **Disclaimer:** For educational and research purposes only. Automated trading carries significant financial risk.

## Quick Start

```python
# Multi-agent analysis pipeline
data = MarketDataService()
fundamentals = FundamentalAnalyst().analyze('AAPL', data.get_fundamentals('AAPL'))
technicals = TechnicalAnalyst().analyze('AAPL', data.get_price_history('AAPL'))
sentiment = SentimentAnalyst().analyze('AAPL', data.get_news('AAPL'))
decision = PortfolioManager().decide('AAPL', {
    'fundamental': fundamentals,
    'technical': technicals,
    'sentiment': sentiment,
}, portfolio)
```

## Architecture

- **Market Data Layer** — Yahoo Finance, Alpha Vantage, Polygon APIs
- **Analyst Agents** — Fundamental (earnings, valuation), Technical (RSI, SMA, trends), Sentiment (news, social)
- **Risk Manager** — Position sizing, drawdown limits, sector exposure, correlation checks
- **Portfolio Manager** — Synthesizes analyst signals into BUY/SELL/HOLD decisions
- **Execution Layer** — Paper trading, backtesting framework, performance metrics

## Agent Team

| Agent | Role | Inputs |
|---|---|---|
| Fundamental Analyst | Earnings, margins, valuation | Financial statements, ratios |
| Technical Analyst | Price trends, momentum | OHLCV data, indicators |
| Sentiment Analyst | News tone, social buzz | News feed, social media |
| Risk Manager | Position limits, exposure | Portfolio state, correlations |
| Portfolio Manager | Final decision synthesis | All analyst outputs |

## Installation

### Claude Code

```bash
cp -R ai-agents/trading-agent-builder ~/.claude/skills/trading-agent-builder
```

### Cursor

```bash
cp -R ai-agents/trading-agent-builder ~/.cursor/skills/trading-agent-builder
```
