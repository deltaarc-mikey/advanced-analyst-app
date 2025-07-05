import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import contextlib
import requests
import feedparser
import openai
from googleapiclient.discovery import build
import traceback

# --- Page Configuration ---
st.set_page_config(layout="wide")
st.title("📊 Delta Ghost AI Trade Engine")
st.markdown("Built with Gemini + ChatGPT + Unusual Whales Intelligence")

# --- Chart with RSI and SMA ---
def generate_technical_chart(tickers_string):
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
    if not tickers:
        return "No tickers provided."

    raw_data = yf.download(tickers, period='6mo', progress=False)
    if raw_data.empty:
        return f"Could not find data for: {', '.join(tickers)}."

    fig, ax = plt.subplots(figsize=(12, 6))
    for ticker in tickers:
        if ticker in raw_data['Adj Close']:
            prices = raw_data['Adj Close'][ticker].dropna()
        else:
            prices = raw_data['Adj Close'].dropna()

        sma_20 = prices.rolling(window=20).mean()
        sma_50 = prices.rolling(window=50).mean()
        rsi = 100 - (100 / (1 + prices.pct_change().rolling(window=14).mean() / prices.pct_change().rolling(window=14).std()))

        ax.plot(prices.index, prices, label=f'{ticker} Price')
        ax.plot(sma_20.index, sma_20, linestyle='--', label=f'{ticker} SMA 20')
        ax.plot(sma_50.index, sma_50, linestyle=':', label=f'{ticker} SMA 50')

    ax.set_title('Price + SMA + RSI (6mo)', fontsize=16)
    ax.set_ylabel('Price (USD)')
    ax.grid(True)
    ax.legend()
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

# --- Google News Tool ---
def Google_Search_for_news(query):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        cse_id = st.secrets["GOOGLE_CSE_ID"]
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=5).execute()
        if 'items' in res:
            results = [f"**{item['title']}**\n{item['link']}\n> {item['snippet']}" for item in res['items']]
            return "\n---\n".join(results)
        return f"No results found for: {query}"
    except Exception as e:
        return f"Error searching Google: {e}"

# --- ChatGPT Response Tool ---
def get_chatgpt_response(prompt):
    try:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"ChatGPT Error: {e}"

# --- Finviz RSS Feed Loader ---
def get_finviz_rss():
    feed_url = "https://finviz.com/feed.ashx"
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        return "No RSS entries found."
    output = []
    for entry in feed.entries[:5]:
        output.append(f"**{entry.title}**\n{entry.link}")
    return "\n---\n".join(output)

# --- Unusual Whales Scanner ---
def fetch_uoa_from_unusualwhales(ticker):
    try:
        api_key = st.secrets["UNUSUALWHALES_API_KEY"]
        url = f"https://api.unusualwhales.com/api/historic_chains?ticker={ticker}"
        headers = {"Authorization": f"Bearer {api_key}"}
        res = requests.get(url, headers=headers)
        data = res.json()
        if not data.get("chains"):
            return "No options flow data found."
        table = pd.DataFrame(data["chains"])[:10]
        return table
    except Exception as e:
        return f"Error fetching UOA: {e}"

# --- UI Tabs ---
tabs = st.tabs(["🔍 Screener & Charts", "🧠 AI Trade Signal Center", "📈 Options & Uploads"])

# --- Tab 1 ---
with tabs[0]:
    st.header("Step 1: Screener & Technical Charts")
    screener_input = st.text_area("Paste top tickers:", "NVDA, AMD, VRT")
    if st.button("📊 Show Chart"):
        result = generate_technical_chart(screener_input)
        if isinstance(result, str):
            st.error(result)
        else:
            st.image(result)

    st.markdown("---")
    st.subheader("📈 Finviz Feed")
    if st.button("Load Finviz RSS"):
        st.markdown(get_finviz_rss())

    st.markdown("---")
    st.subheader("📡 Unusual Whales Flow")
    uoa_ticker = st.text_input("Enter ticker for flow:", "VRT")
    if st.button("🔍 Get UOA"):
        result = fetch_uoa_from_unusualwhales(uoa_ticker)
        if isinstance(result, pd.DataFrame):
            st.dataframe(result)
        else:
            st.error(result)

# --- Tab 2 ---
with tabs[1]:
    st.header("🧠 AI Trade Signal Center")
    user_prompt = st.text_area("Ask ChatGPT for Trade Ideas:", "Which ticker from NVDA, AMD, VRT has best setup today?")
    if st.button("Run ChatGPT"):
        response = get_chatgpt_response(user_prompt)
        st.markdown("**ChatGPT Response:**")
        st.markdown(response)

    gemini_prompt = st.text_area("Ask Gemini (via Google CSE):", "Recent sentiment for NVDA stock")
    if st.button("Run Gemini"):
        result = Google_Search_for_news(gemini_prompt)
        st.markdown("**Gemini Summary:**")
        st.markdown(result)

# --- Tab 3 ---
with tabs[2]:
    st.header("📤 Upload Options Chain CSV or Screenshot")
    uploaded_file = st.file_uploader("Upload options chain file (CSV or Image)", type=["csv", "png", "jpg", "jpeg"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
        else:
            st.image(uploaded_file)

    st.markdown("---")
    st.subheader("Example Trade Ideas")
    st.markdown("""
    **1. May 16 $85 Call**  
    📈 Price: ~$4.68 | OI: 559 | IV: Moderate  
    🔧 Strategy: Buy Call or 85/90 Debit Spread

    **2. May 2 $84/$86 Debit Spread**  
    🎯 Breakeven: $85.31 | Max Profit: $2.00

    **3. May 30 $90 Call**  
    🕒 Earnings Swing Setup | High IV  
    """)

    st.markdown("---")
    st.subheader("Send Summary")
    if st.button("Create Summary"):
        st.success("Summary ready for SMS or email:")
        st.code("Buy VRT May 16 $85 Call @ $4.68. Use debit spread (85/90) if IV rises.")
        st.code("Short-term: Buy May 2 $84/$86 Call Spread for breakout. Max risk $1.31, reward $2.00.")
        st.code("Swing: Buy May 30 $90C for trend extension into earnings.")
