# delta_ghost_dashboard.py
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import pandas_ta as ta
import datetime
import praw
from pytrends.request import TrendReq
import io

# --- SETUP ---
st.set_page_config(layout="wide")
st.title("📊 Delta Ghost AI Trading Dashboard")

# --- REDDIT CONFIG ---
reddit = praw.Reddit(
    client_id=st.secrets["REDDIT_CLIENT_ID"],
    client_secret=st.secrets["REDDIT_CLIENT_SECRET"],
    user_agent=st.secrets["REDDIT_USER_AGENT"]
)

# --- GOOGLE TRENDS SETUP ---
pytrends = TrendReq(hl='en-US', tz=360)

# --- TICKER INPUT ---
st.header("📈 Stock Price and Indicator Chart")
ticker_input = st.text_input("Enter ticker(s):", value="AAPL, TSLA")

def get_price_chart(tickers):
    tickers = [t.strip().upper() for t in tickers.split(',') if t.strip()]
    df = yf.download(tickers, period="6mo")['Adj Close']
    if isinstance(df, pd.Series):
        df = df.to_frame()

    fig, ax = plt.subplots(figsize=(12, 6))
    df.plot(ax=ax)
    ax.set_title("Stock Price - Last 6 Months")
    ax.grid(True)
    st.pyplot(fig)

    return df

if st.button("Generate Chart"):
    chart_data = get_price_chart(ticker_input)
    if len(chart_data.columns) == 1:
        ticker = chart_data.columns[0]
        df = yf.download(ticker, period="6mo")
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=20, append=True)

        fig2, ax2 = plt.subplots(figsize=(12, 6))
        df[['Adj Close', 'SMA_20']].plot(ax=ax2)
        ax2.set_title(f"{ticker} with SMA")
        ax2.grid(True)
        st.pyplot(fig2)

        fig3, ax3 = plt.subplots(figsize=(12, 3))
        df['RSI_14'].plot(ax=ax3, color='orange')
        ax3.axhline(70, color='red', linestyle='--')
        ax3.axhline(30, color='green', linestyle='--')
        ax3.set_title("RSI Indicator")
        st.pyplot(fig3)

# --- REDDIT SENTIMENT ---
st.header("📢 Reddit Sentiment Scanner")
subreddits = ["stocks", "wallstreetbets", "options"]
sentiment_results = []

def scan_reddit():
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        for post in subreddit.hot(limit=15):
            sentiment_results.append({
                "Subreddit": sub,
                "Title": post.title,
                "Score": post.score,
                "Comments": post.num_comments,
                "URL": post.url
            })
    return pd.DataFrame(sentiment_results)

if st.button("Scan Reddit Now"):
    st.info("Fetching sentiment... this may take a moment.")
    reddit_df = scan_reddit()
    st.dataframe(reddit_df)

# --- GOOGLE TRENDS ---
st.header("🌐 Google Trends")
topics = st.text_input("Enter topic(s) for trend scan (comma-separated):", value="AI stocks, Nvidia, inflation")

def fetch_google_trends(keywords):
    kw_list = [k.strip() for k in keywords.split(',') if k.strip()]
    pytrends.build_payload(kw_list, cat=0, timeframe='today 3-m', geo='US')
    return pytrends.interest_over_time()

if st.button("Fetch Google Trends"):
    trends_data = fetch_google_trends(topics)
    if not trends_data.empty:
        st.line_chart(trends_data.drop(columns=['isPartial']))
    else:
        st.warning("No trend data available for those terms.")

# --- SUMMARY ---
st.markdown("---")
st.caption("Powered by Delta Ghost — Reddit, Google Trends, AI Intelligence, and Technical Analysis")
