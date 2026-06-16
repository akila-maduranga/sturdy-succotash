# AutoTrader — AI Crypto Trading Bot

A fully Dockerized, AI-powered cryptocurrency spot trading bot designed to trade with low balances (e.g. $10 USDT) on Binance. The system combines Fibonacci level calculation, candlestick/chart pattern recognition, and OpenRouter AI analysis to make trading decisions, all managed through a premium Web UI.

---

## 🚀 Key Features

1. **Multi-Signal Strategy Consensus**:
   - **Fibonacci Retracement/Extension**: Dynamically detects swing points and golden zones (38.2%, 50%, 61.8%).
   - **Pattern Recognition**: Detects candlestick patterns (Hammer, Engulfing, Morning/Evening Star) and technical indicator signals (RSI, MACD, EMA).
   - **OpenRouter AI Analysis**: Sends clean market snapshots (indicators + Fibonacci + patterns) to Gemini Flash 1.5 or Claude 3.5 to get structured trade plans.
   - **Consensus**: Trade execution requires a custom threshold of these indicators (e.g., 2/3 or 3/3 agreement).

2. **Strict Risk Management**:
   - **Position Sizing**: Trades are sized to risk only 1-2% of your balance per trade.
   - **ATR-Based Stop Loss**: Calculates stop loss dynamically at `1.5x ATR`.
   - **Take Profit (Minimum 2:1 RR)**: Sets target to at least double the risk size.
   - **Daily Drawdown Protection**: Bot pauses automatically if daily losses exceed 5%.
   - **Min-Notional Validation**: Validates minimum order amounts to prevent exchange rejections on tiny balances.

3. **Premium Web UI**:
   - **Live P&L & Balance Tracking**
   - **Interactive Chart**: Real-time candle data with custom Fibonacci level overlays.
   - **AI Analysis Panel**: Shows the detailed reasoning and confidence level of the AI.
   - **Risk Panel**: Sliders to adjust risk per trade, daily stop-losses, and AI confidence thresholds.

---

## 🛠️ Setup & Deployment Guide

Follow these steps to deploy and run the bot on your VPS:

### 1. Prerequisites
- Docker and Docker Compose installed on your VPS.
- An OpenRouter API Key.
- A Binance API Key (with **Enable Spot & Margin Trading** enabled if you plan to trade live).

### 2. Configure Environment Variables
Create a `.env` file in the root directory (you can copy the provided `.env.example` as a starting point):

```bash
cp .env.example .env
```

Open `.env` and fill in your settings:
```env
# Python Path (Required for module imports)
PYTHONPATH=/app

# Binance API (Your API key is preconfigured, add the secret here)
EXCHANGE_API_KEY=bCclTSqKQiLAU7f0cq1EhLu8JCfZVHW56qUjXBDO0KmkmwZhPtswEcMVZQGtlVnd
EXCHANGE_API_SECRET=your_binance_api_secret

# Simulation or Live settings
TESTNET=false      # Set to true to run on Binance Testnet
READ_ONLY=true     # Set to true to run paper trading/simulation mode. Set to false for live execution.

# OpenRouter AI
OPENROUTER_API_KEY=your_openrouter_api_key
AI_MODEL=google/gemini-flash-1.5

# Database Settings (Change passwords in production)
POSTGRES_USER=trader
POSTGRES_PASSWORD=trader_secret_2024
POSTGRES_DB=tradingbot
DATABASE_URL=postgresql+asyncpg://trader:trader_secret_2024@db:5432/tradingbot
```

### 3. Build & Run
Run the following command to start all services in the background:

```bash
docker compose up --build -d
```

This starts:
- **Nginx Reverse Proxy** (listening on Port `80`)
- **Frontend SPA** (Port `3000`)
- **FastAPI API Server** (Port `8000`)
- **Celery Worker & Celery Beat** (Periodic scheduler running strategy checks every 5 mins)
- **PostgreSQL Database** (Trade logs & settings)
- **Redis Cache** (Price updates & message broker)

To verify all containers are running successfully:
```bash
docker compose ps
```

### 4. Access the Dashboard
Open your web browser and navigate to:
```
http://your-vps-ip
```

### 5. Troubleshooting & Useful Commands
- **View Bot Execution Logs**:
  ```bash
  docker compose logs -f worker
  ```
- **View Backend API Logs**:
  ```bash
  docker compose logs -f backend
  ```
- **Restart the Bot/Worker**:
  ```bash
  docker compose restart worker beat
  ```
- **Stop All Services**:
  ```bash
  docker compose down
  ```

---

## 📁 File Structure

- `/backend` — FastAPI application code.
  - `/backend/services` — Core calculation engines (Fibonacci, technical patterns, risk management, and OpenRouter AI analysis).
  - `/backend/workers` — Background scheduling logic (Celery tasks).
- `/frontend` — React/Vite application.
- `/nginx` — Reverse proxy configuration for routing API, WebSocket, and HTTP traffic.
- `docker-compose.yml` — Orchestrates the multi-container stack.
