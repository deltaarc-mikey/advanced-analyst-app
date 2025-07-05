# 📊 Delta Ghost AI Trade Engine — Streamlit App
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import feedparser
import requests
import io
import openai
from streamlit_option_menu import option_menu

# ---------- SETUP ----------
st.set_page_config(layout="wide", page_title="Delta Ghost AI Dashboard")
st.title("📊 Delta Ghost AI Trade Engine")
st.caption("Built with Gemini + ChatGPT + Unusual Whales Intelligence")

# ---------- OPTION MENU ----------
selected = option_menu(
    menu_title=None,
    options=["📈 Screener & Charts", "🤖 AI Trade Signal Center", "📤 Options & Uploads"],
    icons=["bar-chart", "robot", "cloud-upload"],
    orientation="horizontal",
)

# ---------- FUNCTIONS ----------
def load_price_chart(tickers):
    tickers = [x.strip().upper() for x in tickers.split(',') if x.strip()]
    if not tickers:
        st.warning("Please enter at least one ticker.")
        return

    data = yf.download(tickers, period='6mo', progress=False)['Adj Close']
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])

    fig, ax = plt.subplots(figsize=(14, 6))
    for ticker in data.columns:
        prices = data[ticker].dropna()
        rsi = ta.rsi(prices)
        sma = ta.sma(prices)
        ax.plot(prices.index, prices, label=ticker)
        ax.plot(rsi.index, rsi, linestyle='--', label=f"RSI - {ticker}")
        ax.plot(sma.index, sma, linestyle=':', label=f"SMA - {ticker}")

    ax.set_title("Price with RSI & SMA Overlays")
    ax.legend()
    st.pyplot(fig)

# ---------- UOA UNUSUAL WHALES ----------
def fetch_unusual_whales_flow(ticker):
    api_key = st.secrets["UW_API_KEY"]
    endpoint = f"https://phx.unusualwhales.com/api/historic_chains/{ticker.upper()}"
    headers = {"Authorization": f"Bearer {api_key}"}
    res = requests.get(endpoint, headers=headers)
    if res.status_code == 200:
        data = res.json()
        df = pd.DataFrame(data)
        st.dataframe(df.head(20))
    else:
        st.error("Failed to retrieve UOA data. Check API key or ticker.")

# ---------- FINVIZ FEED ----------
def load_finviz_rss():
    url = "https://finviz.com/feed.ashx"
    d = feedparser.parse(url)
    if d.entries:
        for entry in d.entries[:5]:
            st.markdown(f"**[{entry.title}]({entry.link})**\n\n{entry.description}")
    else:
        st.write("No RSS entries found.")

# ---------- LAYOUT: SCREENER & CHARTS ----------
if selected == "📈 Screener & Charts":
    st.subheader("Step 1: Screener & Technical Charts")
    tickers = st.text_area("Paste top tickers:", "NVDA, AMD, VRT")
    if st.button("📊 Show Chart"):
        load_price_chart(tickers)

    st.divider()
    st.subheader("📉 Finviz Feed")
    if st.button("Load Finviz RSS"):
        load_finviz_rss()

    st.divider()
    st.subheader("🛰️ Unusual Whales Flow")
    ticker = st.text_input("Enter ticker for flow:", "VRT")
    if st.button("📡 Get UOA"):
        fetch_unusual_whales_flow(ticker)

# ---------- LAYOUT: AI TRADE SIGNAL CENTER ----------
elif selected == "🤖 AI Trade Signal Center":
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Gemini Analysis ✨")
        st.write("Paste summary or context for Gemini below:")
        gemini_input = st.text_area("Gemini Input", "Today’s top movers include TSLA and PLTR…")
        if st.button("Analyze with Gemini"):
            st.success("Gemini output placeholder...")

    with col2:
        st.subheader("ChatGPT Analysis 🧠")
        st.write("Paste summary or context for GPT below:")
        gpt_input = st.text_area("GPT Input", "Show sentiment on TSLA vs PLTR")
        if st.button("Analyze with ChatGPT"):
            st.success("ChatGPT output placeholder...")

# ---------- LAYOUT: OPTIONS + UPLOADS ----------
elif selected == "📤 Options & Uploads":
    st.subheader("Upload UOA CSVs or Custom Files")
    uploaded_file = st.file_uploader("Choose CSV file to upload:", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
