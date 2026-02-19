"""
Streamlit Trading Dashboard
Run with:

streamlit run bot/dashboard.py
"""

import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import requests
from decimal import Decimal

from client import BinanceClient


# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Trading Bot Dashboard",
    layout="wide",
    page_icon="📈"
)


# ---------------------------------------------------
# CLIENT
# ---------------------------------------------------

def get_client():
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")

    return BinanceClient(api_key, api_secret)


client = get_client()


# ---------------------------------------------------
# PRICE DATA
# ---------------------------------------------------

def get_price(symbol="BTCUSDT"):
    url = f"https://testnet.binance.vision/api/v3/ticker/price?symbol={symbol}"
    return float(requests.get(url).json()["price"])


def get_klines(symbol="BTCUSDT"):
    url = f"https://testnet.binance.vision/api/v3/klines"
    params = {"symbol": symbol, "interval": "1m", "limit": 100}

    data = requests.get(url, params=params).json()

    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "num_trades", "taker_base",
        "taker_quote", "ignore"
    ])

    df["close"] = df["close"].astype(float)
    df["time"] = pd.to_datetime(df["time"], unit="ms")

    return df


# ---------------------------------------------------
# ACCOUNT
# ---------------------------------------------------

def get_balances():
    account = client.get_account()
    balances = account.get("balances", [])

    rows = []
    for b in balances:
        free = float(b["free"])
        locked = float(b["locked"])
        total = free + locked

        if total > 0:
            rows.append([b["asset"], free, locked, total])

    df = pd.DataFrame(rows, columns=["Asset", "Free", "Locked", "Total"])
    return df


# ---------------------------------------------------
# TRADE HISTORY (Mock using open orders)
# ---------------------------------------------------

def get_orders(symbol="BTCUSDT"):
    orders = client.get_open_orders(symbol)

    if not orders:
        return pd.DataFrame()

    rows = []
    for o in orders:
        rows.append([
            o["symbol"],
            o["side"],
            o["type"],
            o["price"],
            o["origQty"],
            o["status"]
        ])

    return pd.DataFrame(rows, columns=[
        "Symbol", "Side", "Type", "Price", "Qty", "Status"
    ])


# ---------------------------------------------------
# PNL CALC
# ---------------------------------------------------

def calculate_pnl():
    balances = get_balances()

    usdt = balances.loc[balances.Asset == "USDT", "Total"].sum()
    btc = balances.loc[balances.Asset == "BTC", "Total"].sum()

    price = get_price()

    portfolio_value = usdt + btc * price

    return portfolio_value


# ---------------------------------------------------
# UI
# ---------------------------------------------------

st.title("📈 Binance Trading Dashboard")

col1, col2, col3 = st.columns(3)

price = get_price()

with col1:
    st.metric("BTC Price", f"${price:,.2f}")

with col2:
    pnl = calculate_pnl()
    st.metric("Portfolio Value (USDT)", f"{pnl:,.2f}")

with col3:
    st.metric("Environment", "Testnet")


# ---------------------------------------------------
# CHART
# ---------------------------------------------------

st.subheader("Live BTC Chart")

df = get_klines()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["time"],
    y=df["close"],
    mode="lines",
    name="BTC Price"
))

st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------
# BALANCES
# ---------------------------------------------------

st.subheader("Account Balances")

balances = get_balances()
st.dataframe(balances, use_container_width=True)


# ---------------------------------------------------
# ORDERS
# ---------------------------------------------------

st.subheader("Open Orders")

orders = get_orders()
st.dataframe(orders, use_container_width=True)


# ---------------------------------------------------
# PLACE ORDER
# ---------------------------------------------------

st.subheader("Place Order")

symbol = st.text_input("Symbol", "BTCUSDT")
side = st.selectbox("Side", ["BUY", "SELL"])
order_type = st.selectbox("Type", ["MARKET", "LIMIT"])
qty = st.number_input("Quantity", value=0.001)

price_input = None

if order_type == "LIMIT":
    price_input = st.number_input("Price", value=70000.0)

if st.button("Submit Order"):

    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=Decimal(str(qty)),
            price=Decimal(str(price_input)) if price_input else None,
        )

        st.success(f"Order Placed: {response.get('status')}")

    except Exception as e:
        st.error(str(e))


# ---------------------------------------------------
# REFRESH
# ---------------------------------------------------

st.button("Refresh")
