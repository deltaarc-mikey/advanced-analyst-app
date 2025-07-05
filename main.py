import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import io
import pandas as pd
import contextlib
from googleapiclient.discovery import build
import traceback # Import for detailed error logging

plt.switch_backend('agg')

# --- Tool Functions ---
# The other functions (generate_price_chart, Google Search_for_news) are unchanged
# For brevity, I am only showing the new heatmap function and the UI
def generate_price_chart(tickers_string):
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
    if not tickers: return "No tickers provided."
    raw_data = yf.download(tickers, period='1y', progress=False)
    if raw_data.empty: return f"Could not find any data for the tickers: {', '.join(tickers)}."
    if 'Adj Close' in raw_data.columns:
        price_data, price_label = raw_data['Adj Close'], 'Adjusted Close Price'
    elif 'Close' in raw_data.columns:
        price_data, price_label = raw_data['Close'], 'Close Price'
    else: return "Could not find 'Adj Close' or 'Close' columns."
    if isinstance(price_data, pd.Series): price_data = price_data.to_frame(name=tickers[0])
    price_data.dropna(axis=1, how='all', inplace=True)
    if price_data.empty: return f"All tickers provided were invalid or had no data: {', '.join(tickers)}."
    fig, ax = plt.subplots(figsize=(12, 7)); price_data.plot(ax=ax)
    ax.set_title('Stock Price Comparison (Last Year)', fontsize=16); ax.set_ylabel(f'{price_label} (USD)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12); ax.grid(True); ax.legend(title='Tickers')
    buf = io.BytesIO(); fig.savefig(buf, format='png'); buf.seek(0); plt.close(fig)
    return buf

def Google_Search_for_news(query):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]; cse_id = st.secrets["GOOGLE_CSE_ID"]
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=5).execute()
        if 'items' in res:
            formatted_results = []
            for item in res['items']:
                title = item.get('title', 'No Title'); link = item.get('link', '#'); snippet = item.get('snippet', 'No snippet available.').replace('\n', '')
                formatted_results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n---")
            return "\n".join(formatted_results)
        else: return f"No search results found for '{query}'."
    except Exception as e: return f"An error occurred during the search: {e}"

# vvv DEBUG VERSION OF HEATMAP FUNCTION vvv
def generate_technical_heatmap(tickers_string):
    """
    This is a debug version to find the root cause of the error.
    It will return a detailed error message instead of a heatmap.
    """
    try:
        tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
        if not tickers: return "No tickers provided."

        indicator_df = pd.DataFrame(index=tickers, columns=['RSI', 'Above_SMA50', 'SMA20_Slope'])

        for ticker in tickers:
            # No more try/except inside the loop so we can see the error
            data = yf.download(ticker, period='4mo', progress=False, auto_adjust=True)
            if data.empty or len(data) < 52:
                indicator_df.loc[ticker] = [pd.NA, pd.NA, pd.NA]
                continue

            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss.replace(0, 1e-10) 
            rsi = 100 - (100 / (1 + rs))

            sma20 = data['Close'].rolling(window=20).mean()
            sma50 = data['Close'].rolling(window=50).mean()

            latest_close = data['Close'].dropna().iloc[-1]
            rsi_val = rsi.dropna().iloc[-1]
            sma50_val = sma50.dropna().iloc[-1]

            last_two_sma20 = sma20.dropna().iloc[-2:]
            current_sma20_val, prev_sma20_val = last_two_sma20.iloc[1], last_two_sma20.iloc[0]

            indicator_df.loc[ticker, 'RSI'] = rsi_val
            indicator_df.loc[ticker, 'Above_SMA50'] = 'Yes' if latest_close > sma50_val else 'No'
            indicator_df.loc[ticker, 'SMA20_Slope'] = 'Up' if current_sma20_val > prev_sma20_val else 'Down'

        indicator_df.dropna(how='all', inplace=True)
        if indicator_df.empty: return "Could not generate heatmap for any of the given tickers."

        # This part will likely not be reached, the error happens before this
        fig, ax = plt.subplots(figsize=(10, len(indicator_df) * 0.5)); ax.axis('off')
        return "This part was not reached, error is in calculation."

    except Exception as e:
        # THIS IS THE IMPORTANT PART
        # Return the actual error message so we can see it.
        return f"A critical error occurred: {e}\n\nTraceback:\n{traceback.format_exc()}"

# --- Streamlit User Interface (is unchanged) ---
st.set_page_config(layout="wide")
st.title("📈 Advanced AI Analyst")
st.header("Comparative Price Chart")
chart_ticker_input = st.text_input("Enter stock tickers separated by commas:", "AAPL, MSFT, NVDA", key="chart_input")
if st.button("Generate Chart"):
    if chart_ticker_input:
        with st.spinner("Generating chart..."):
            result = generate_price_chart(chart_ticker_input)
            if isinstance(result, str): st.error(result)
            else: st.image(result)
else: st.warning("Please enter at least one ticker for the chart.")
st.markdown("---")
st.header("📊 Technical Indicators Heatmap")
heatmap_ticker_input = st.text_input("Enter stock tickers for the heatmap:", "TSLA,GOOG", key="heatmap_input")
if st.button("Generate Heatmap"):
    if heatmap_ticker_input:
        with st.spinner("Generating heatmap..."):
            result = generate_technical_heatmap(heatmap_ticker_input)
            if isinstance(result, str): st.error(result)
            else: st.image(result)
else: st.
