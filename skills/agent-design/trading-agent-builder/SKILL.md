---
name: "trading-agent-builder"
description: "Build AI-powered trading and financial analysis agents using multi-agent architectures with LLMs"
---

# Trading Agent Builder

**Tier:** POWERFUL
**Category:** AI Agents
**Domain:** Financial AI / Trading Systems / Multi-Agent Finance

## Overview

Build multi-agent AI trading systems that combine LLM reasoning with quantitative analysis. This covers the full pipeline: market data ingestion, multi-agent analysis (fundamentals, technicals, sentiment, risk), signal generation, backtesting, and paper trading. Inspired by the TradingAgents framework trending on GitHub.

**⚠️ DISCLAIMER:** This skill is for educational and research purposes. Automated trading carries significant financial risk. Always paper-trade first, use proper risk management, and never trade money you can't afford to lose.

## When to Use

- Building a multi-agent trading research system
- Creating AI-powered financial analysis pipelines
- Implementing sentiment analysis for market signals
- Building portfolio optimization with LLM reasoning
- Creating backtesting frameworks for AI strategies
- Designing risk management systems with AI guardrails
- Building market monitoring and alerting agents

## Multi-Agent Trading Architecture

```
┌─────────────────────────────────────────────────┐
│              Market Data Layer                   │
│  APIs: Yahoo Finance, Alpha Vantage, Polygon    │
│  Feeds: Price, Volume, News, SEC Filings        │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│            Analyst Agent Team                    │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │Fundamental│ │Technical │ │   Sentiment      ││
│  │ Analyst   │ │ Analyst  │ │   Analyst        ││
│  │(Financials│ │(Charts,  │ │(News, Reddit,    ││
│  │ Earnings) │ │Indicators│ │ Twitter, filings)││
│  └────┬──────┘ └────┬─────┘ └────┬─────────────┘│
│       │             │             │              │
│  ┌────┴─────────────┴─────────────┴─────────┐   │
│  │         Risk Manager Agent                │   │
│  │  (Position sizing, drawdown limits,       │   │
│  │   correlation checks, exposure limits)    │   │
│  └────────────────┬──────────────────────────┘   │
└───────────────────┤──────────────────────────────┘
                    │
┌───────────────────┴──────────────────────────────┐
│            Portfolio Manager Agent                │
│  (Final signal: BUY / SELL / HOLD + sizing)      │
│  Weighs analyst opinions + risk constraints       │
└───────────────────┬──────────────────────────────┘
                    │
┌───────────────────┴──────────────────────────────┐
│              Execution Layer                      │
│  Paper Trading → Backtesting → (Live optional)    │
└──────────────────────────────────────────────────┘
```

## Implementation

### 1. Market Data Layer

```python
import yfinance as yf
from datetime import datetime, timedelta

class MarketDataService:
    def get_price_history(self, symbol: str, period: str = '1y') -> dict:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        return {
            'prices': hist['Close'].tolist(),
            'volumes': hist['Volume'].tolist(),
            'dates': [d.strftime('%Y-%m-%d') for d in hist.index],
            'current_price': hist['Close'].iloc[-1],
            'change_1d': (hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100,
        }

    def get_fundamentals(self, symbol: str) -> dict:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            'pe_ratio': info.get('trailingPE'),
            'market_cap': info.get('marketCap'),
            'revenue_growth': info.get('revenueGrowth'),
            'profit_margins': info.get('profitMargins'),
            'debt_to_equity': info.get('debtToEquity'),
            'free_cash_flow': info.get('freeCashflow'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
        }

    def get_news(self, symbol: str) -> list:
        ticker = yf.Ticker(symbol)
        return [{'title': n['title'], 'link': n['link'],
                 'published': n.get('providerPublishTime')}
                for n in ticker.news[:10]]
```

### 2. Analyst Agents

```python
from openai import OpenAI

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_KEY)

class FundamentalAnalyst:
    SYSTEM = """You are a senior fundamental analyst. Analyze financials and
    provide a signal: BULLISH, BEARISH, or NEUTRAL with confidence 0-100.
    Focus on: earnings quality, revenue growth, margin trends, valuation,
    competitive moat, and balance sheet strength."""

    def analyze(self, symbol: str, data: dict) -> dict:
        response = client.chat.completions.create(
            model="anthropic/claude-sonnet-4-20250514",
            messages=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": f"Analyze {symbol}:\n{json.dumps(data)}"},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

class TechnicalAnalyst:
    SYSTEM = """You are a senior technical analyst. Analyze price action and
    indicators. Provide signal: BULLISH, BEARISH, or NEUTRAL with confidence.
    Focus on: trend direction, support/resistance, momentum, volume patterns."""

    def analyze(self, symbol: str, prices: list, volumes: list) -> dict:
        # Calculate indicators before sending to LLM
        indicators = {
            'sma_20': sum(prices[-20:]) / 20,
            'sma_50': sum(prices[-50:]) / 50 if len(prices) >= 50 else None,
            'rsi_14': self._calculate_rsi(prices, 14),
            'price_vs_sma20': (prices[-1] / (sum(prices[-20:]) / 20) - 1) * 100,
            'volume_trend': 'increasing' if volumes[-1] > sum(volumes[-5:]) / 5 else 'decreasing',
        }
        response = client.chat.completions.create(
            model="anthropic/claude-sonnet-4-20250514",
            messages=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": f"Analyze {symbol}:\nIndicators: {json.dumps(indicators)}\nRecent prices: {prices[-30:]}"},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

class SentimentAnalyst:
    SYSTEM = """You are a market sentiment analyst. Analyze news and social
    sentiment. Provide signal: BULLISH, BEARISH, or NEUTRAL with confidence.
    Focus on: news tone, social media buzz, insider activity, analyst ratings."""

    def analyze(self, symbol: str, news: list) -> dict:
        response = client.chat.completions.create(
            model="anthropic/claude-sonnet-4-20250514",
            messages=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": f"Sentiment for {symbol}:\n{json.dumps(news)}"},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
```

### 3. Portfolio Manager (Decision Synthesis)

```python
class PortfolioManager:
    SYSTEM = """You are a portfolio manager synthesizing analyst opinions into
    a final trading decision. You must consider:
    1. Consensus across analysts (agreement = higher conviction)
    2. Risk constraints (max position size, sector exposure)
    3. Current portfolio state
    4. Market regime (bull/bear/sideways)
    
    Output: { action: BUY|SELL|HOLD, size: percentage, reasoning: string }"""

    def decide(self, symbol: str, analyses: dict, portfolio: dict) -> dict:
        response = client.chat.completions.create(
            model="anthropic/claude-sonnet-4-20250514",
            messages=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": f"""
Symbol: {symbol}
Fundamental: {json.dumps(analyses['fundamental'])}
Technical: {json.dumps(analyses['technical'])}
Sentiment: {json.dumps(analyses['sentiment'])}
Current Portfolio: {json.dumps(portfolio)}
Max position size: 10% of portfolio
                """},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
```

### 4. Risk Management

```python
class RiskManager:
    def __init__(self, max_position_pct=0.10, max_drawdown_pct=0.15, max_sector_pct=0.30):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_sector_pct = max_sector_pct

    def validate_trade(self, trade: dict, portfolio: dict) -> dict:
        checks = {
            'position_size_ok': trade['size'] <= self.max_position_pct,
            'drawdown_ok': portfolio['current_drawdown'] < self.max_drawdown_pct,
            'sector_ok': self._check_sector_exposure(trade, portfolio),
            'correlation_ok': self._check_correlation(trade, portfolio),
        }
        checks['approved'] = all(checks.values())
        if not checks['approved']:
            checks['adjusted_size'] = min(trade['size'], self.max_position_pct / 2)
        return checks
```

## Backtesting Framework

```python
class Backtester:
    def run(self, strategy, symbols: list, start_date: str, end_date: str):
        portfolio = {'cash': 100000, 'positions': {}, 'history': []}
        
        for date in self._trading_days(start_date, end_date):
            for symbol in symbols:
                data = self._get_historical_data(symbol, date)
                signal = strategy.analyze(symbol, data)
                
                if signal['action'] == 'BUY':
                    self._execute_buy(portfolio, symbol, signal, data)
                elif signal['action'] == 'SELL':
                    self._execute_sell(portfolio, symbol, data)
                
                portfolio['history'].append({
                    'date': date, 'total_value': self._portfolio_value(portfolio, date),
                })
        
        return self._calculate_metrics(portfolio)
```

## Common Pitfalls

1. **Overfitting to historical data** — Backtest on out-of-sample data
2. **Ignoring transaction costs** — Include slippage, commissions, spread
3. **No risk limits** — Always implement position sizing and stop losses
4. **LLM hallucinating numbers** — Feed actual data to LLM, don't ask it to recall
5. **Real-time bias** — Backtests must only use data available at that point in time
6. **Survivorship bias** — Include delisted stocks in historical analysis

## Compliance Notes

- This is for research and education only
- Paper trade extensively before any live trading
- Consult a financial advisor for real investments
- Comply with local securities regulations
- Log all agent decisions for audit trails
