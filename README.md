# ◈ Binance Futures Testnet Trading Bot + Dashboard

A production-grade Python trading bot for the **Binance Futures Testnet (USDT-M)** with:

✅ CLI trading interface
✅ Streamlit web dashboard
✅ Structured logging
✅ Clean layered architecture
✅ Real account + order monitoring

---

## 🚀 Features

| Feature         | Details                                  |
| --------------- | ---------------------------------------- |
| **Trading**     | MARKET, LIMIT, STOP_MARKET, STOP_LIMIT   |
| **CLI**         | Built with Typer + Rich                  |
| **Dashboard**   | Streamlit live trading UI                |
| **Validation**  | Strict input validation before API calls |
| **Logging**     | Colored console + structured log files   |
| **Account**     | Balances, portfolio value, open orders   |
| **Analytics**   | Portfolio value & PnL calculations       |
| **Charts**      | Live BTC price visualization             |
| **Environment** | Binance Testnet (safe — no real money)   |

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── orders.py
│   ├── validators.py
│   ├── logging_config.py
│   ├── analytics.py       # Portfolio value & PnL calculations
│   ├── cli.py
│   └── dashboard.py       # Streamlit dashboard
│
├── logs/
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1️⃣ Get Binance Testnet API Keys

1. Visit https://testnet.binance.vision
2. Login using your GitHub account
3. Generate an API Key
4. Copy your API Key and Secret

> ⚠️ This project uses Binance **Testnet only** — no real funds are involved.

---

### 2️⃣ Clone Repository

```bash
git clone https://github.com/your-username/trading_bot.git
cd trading_bot
```

---

### 3️⃣ Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# .venv\Scripts\activate       # Windows
```

---

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5️⃣ Configure Environment Variables

```bash
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"
```

Optional `.env` usage:

```bash
cp .env.example .env
```

---

## 🧪 CLI Usage

### Check Connection

```bash
python -m bot.cli ping
```

---

### Place MARKET Order

```bash
python -m bot.cli order BTCUSDT --side BUY --type MARKET --qty 0.001
```

---

### Place LIMIT Order

```bash
python -m bot.cli order BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 68000
```

---

### STOP MARKET (Stop Loss)

```bash
python -m bot.cli order BTCUSDT --side SELL --type STOP_MARKET \
  --qty 0.001 --stop-price 65000
```

---

### STOP LIMIT

```bash
python -m bot.cli order BTCUSDT --side SELL --type STOP_LIMIT \
  --qty 0.001 --stop-price 65500 --price 65000
```

---

### Account Information

```bash
python -m bot.cli account
```

---

### Open Orders

```bash
python -m bot.cli open-orders
python -m bot.cli open-orders BTCUSDT
```

---

### Cancel Order

```bash
python -m bot.cli cancel BTCUSDT ORDER_ID
```

---

## 📊 Streamlit Dashboard

Run the web interface:

```bash
streamlit run bot/dashboard.py
```

Then open:

```
http://localhost:8501
```

Dashboard includes:

* Live BTC price
* Portfolio value
* Account balances
* Open orders
* Trading form
* Interactive chart

---

## 🖥 Output Example

```
  ◈ BINANCE FUTURES  ·  TESTNET  ·  TRADING BOT  ◈
  Log → logs/trading_bot_20250614_102201.log

╭─ Order Request ─────────────────────────────╮
│  Symbol        BTCUSDT                      │
│  Side          BUY                          │
│  Order Type    MARKET                       │
│  Quantity      0.001                        │
╰─────────────────────────────────────────────╯

╭─ ✓ Order Placed — FILLED ───────────────────╮
│  Order ID        3947291847                 │
│  Symbol          BTCUSDT                    │
│  Side            BUY                        │
│  Type            MARKET                     │
│  Status          FILLED                     │
│  Orig. Qty       0.001                      │
│  Executed Qty    0.001                      │
│  Avg. Price      67243.50                   │
╰─────────────────────────────────────────────╯
```

---

## 📝 Logging

Logs are stored in:

```
logs/trading_bot_YYYYMMDD_HHMMSS.log
```

Console → INFO level
File → DEBUG level

---

## 🏗 Architecture

```
cli.py          → User interface layer
orders.py       → Trading logic
client.py       → Binance API transport
analytics.py    → Portfolio & PnL calculations
validators.py   → Input validation
logging_config  → Logging utilities
dashboard.py    → Streamlit UI
```

Each layer has a single responsibility for maintainability.

---

## 🔐 Security Notes

* Testnet only (no real funds)
* API keys stored in environment variables
* No credentials stored in code
* HMAC-SHA256 request signing

---

## 📦 Dependencies

* requests
* typer
* rich
* streamlit
* pandas
* plotly
* python-dotenv

---

## ⭐ Future Improvements

* Auto-trading strategies
* EMA / RSI indicators
* Trade history database
* Docker deployment
* Cloud hosting
