import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import contextlib
import requests
from googleapiclient.discovery import build
import traceback

# --- Page Configuration ---
st.set_page_config(layout="wide")
st.title("📊 Delta Ghost AI Trade Engine")
st.markdown("Built with Gemini + Technical Analysis + Options Intelligence")

# --- Price Chart Tool ---
def generate_price_chart(tickers_string):
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
    if not tickers:
        return "No tickers provided."

    raw_data = yf.download(tickers, period='6mo', progress=False)
    if raw_data.empty:
        return f"Could not find any data for the tickers: {', '.join(tickers)}."

    price_data = raw_data['Adj Close'] if 'Adj Close' in raw_data.columns else raw_data['Close']
    if isinstance(price_data, pd.Series):
        price_data = price_data.to_frame(name=tickers[0])

    price_data.dropna(axis=1, how='all', inplace=True)
    if price_data.empty:
        return f"All tickers provided were invalid or had no data."

    fig, ax = plt.subplots(figsize=(12, 6))
    price_data.plot(ax=ax)
    ax.set_title('Stock Price Comparison (Last 6 Months)', fontsize=16)
    ax.set_ylabel('Price (USD)')
    ax.set_xlabel('Date')
    ax.grid(True)
    ax.legend(title='Ticker')
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

# --- Screener Input ---
st.header("Step 1: Paste Screener Results")
screener_input = st.text_area("Paste top 100 tickers (comma-separated)", "NVDA, AMD, VRT, SOFI, HIMS")
st.markdown("---")

# --- Technical Chart Section ---
st.header("Step 2: Price Chart & Momentum Snapshot")
chart_input = st.text_input("Tickers for charting:", value="VRT, SOFI, NVDA")
if st.button("🔄 Generate Chart"):
    result = generate_price_chart(chart_input)
    if isinstance(result, str):
        st.error(result)
    else:
        st.image(result)
st.markdown("---")

# --- News Scan ---
st.header("Step 3: Catalyst / News Scanner")
news_query = st.text_input("Search recent news about top tickers:", "Vertiv Holdings AI Data Center")
if st.button("🔍 Run News Scan"):
    with st.spinner("Searching..."):
        news_results = Google_Search_for_news(news_query)
        st.markdown(news_results)
st.markdown("---")

# --- Manual Options Chain Upload ---
st.header("Step 4: Upload Options Chain Screenshot or CSV")
uploaded_file = st.file_uploader("Upload options chain file (CSV or Image)", type=["csv", "png", "jpg", "jpeg"])
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
    else:
        st.image(uploaded_file)

st.markdown("---")

# --- Strategy Builder ---
st.header("Step 5: Sample Trade Recommendations")
st.subheader("Top 3 Trades for VRT")
st.markdown("""
**1. May 16 $85 Call**  
Price: ~$4.68 | OI: 559 | IV: Moderate  
📉 *Rationale:* Solid volume, breakout target if VRT continues uptrend  
🔧 *Strategy:* Buy Call or 85/90 Debit Spread

**2. May 2 $84/$86 Call Debit Spread**  
Net Debit: $1.31 | Max Profit: $2.00 | Breakeven: $85.31  
📉 *Short-term move with low risk*

**3. May 30 $90 Call**  
Price: ~$7.65 | Higher IV | Longer setup  
📉 *Use for bullish swing play with earnings catalyst*
""")

# --- Summary Export ---
st.markdown("---")
st.header("📤 Generate Trade Summary")
if st.button("📋 Create Summary"):
    st.success("Summary ready for SMS or email:")
    st.code("Buy VRT May 16 $85 Call @ $4.68. Use debit spread (85/90) if IV rises.")
    st.code("Short-term: Buy May 2 $84/$86 Call Spread for breakout. Max risk $1.31, max reward $2.00.")
    st.code("Swing: Buy May 30 $90C for trend extension into earnings.")
