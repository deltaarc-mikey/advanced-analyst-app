import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import io
import requests
import feedparser
import openai
from googleapiclient.discovery import build
from streamlit_option_menu import option_menu

# --- Streamlit Setup ---
st.set_page_config(page_title="Delta Ghost AI Trade Engine", layout="wide")
st.title("📊 Delta Ghost AI Trade Engine")
st.markdown("Built with Gemini + ChatGPT + Unusual Whales Intelligence")

# --- Sidebar Navigation ---
selected = option_menu(
    menu_title=None,
    options=["Screener & Charts", "AI Trade Signal Center", "Options & Uploads"],
    icons=["graph-up-arrow", "robot", "cloud-upload"],
    orientation="horizontal"
)

# --- Helper Functions ---
def fetch_price_chart(tickers):
    tickers = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    data = yf.download(tickers, period="6mo")
    if 'Adj Close' in data:
        price_data = data['Adj Close']
    else:
        price_data = data['Close']

    fig, ax = plt.subplots(figsize=(12, 6))
    price_data.plot(ax=ax)
    for ticker in tickers:
        try:
            sma_20 = ta.sma(price_data[ticker], length=20)
            rsi_14 = ta.rsi(price_data[ticker], length=14)
            sma_20.plot(ax=ax, linestyle='--', label=f"{ticker} SMA-20")
        except:
            pass
    ax.set_title("Price Chart with SMA Overlay")
    ax.set_xlabel("Date"); ax.set_ylabel("Price (USD)")
    ax.grid(True); ax.legend()
    return fig

# --- Finviz Feed Function ---
def load_finviz_feed():
    url = "https://finviz.com/feed.ashx"
    feed = feedparser.parse(url)
    return feed.entries[:5]

# --- Unusual Whales API Function ---
def get_unusual_whales_flow(ticker):
    try:
        api_key = st.secrets['UW_API_KEY']  # Your Unusual Whales API Key
        url = f"https://phx.unusualwhales.com/api/historic_chains/{ticker}?limit=10"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.DataFrame(response.json()['chains'])
        else:
            return f"Failed to fetch UOA data: {response.status_code}"
    except Exception as e:
        return str(e)

# --- Page 1: Screener & Charts ---
if selected == "Screener & Charts":
    st.header("Step 1: Screener & Technical Charts")
    tickers_input = st.text_area("Paste top tickers:", "NVDA, AMD, VRT")
    if st.button("📈 Show Chart"):
        with st.spinner("Loading chart..."):
            fig = fetch_price_chart(tickers_input)
            st.pyplot(fig)

    st.markdown("---")
    st.subheader("📉 Finviz Feed")
    if st.button("Load Finviz RSS"):
        with st.spinner("Fetching Finviz feed..."):
            entries = load_finviz_feed()
            for e in entries:
                st.markdown(f"**{e.title}**\n\n[{e.link}]({e.link})\n\n---")

    st.markdown("---")
    st.subheader("🛰 Unusual Whales Flow")
    uoa_ticker = st.text_input("Enter ticker for flow:", "VRT")
    if st.button("🚀 Get UOA"):
        uoa_data = get_unusual_whales_flow(uoa_ticker)
        if isinstance(uoa_data, pd.DataFrame):
            st.success("UOA data loaded successfully!")
            st.dataframe(uoa_data.head())
        else:
            st.error(uoa_data)

# --- Page 2: AI Trade Signal Center ---
elif selected == "AI Trade Signal Center":
    st.header("🤖 AI Trade Signal Center")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Gemini Response")
        st.info("(Gemini integration placeholder)")
        st.text_area("Gemini response area", "")

    with col2:
        st.subheader("ChatGPT Response")
        st.info("(ChatGPT integration placeholder)")
        st.text_area("ChatGPT response area", "")

# --- Page 3: Options Uploads ---
elif selected == "Options & Uploads":
    st.header("📦 Options Upload + Tools")
    uploaded_file = st.file_uploader("Upload your CSV file (e.g. Unusual Whales or Barchart export)", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("CSV uploaded successfully!")
        st.dataframe(df.head())
