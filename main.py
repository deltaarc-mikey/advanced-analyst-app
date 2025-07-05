import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import praw
from pytrends.request import TrendReq
from docx import Document
import openai
import requests
from datetime import datetime, timedelta

# ========== CONFIGURATION ==========

# Reddit API
reddit = praw.Reddit(
    client_id="YOUR_REDDIT_CLIENT_ID",
    client_secret="YOUR_REDDIT_CLIENT_SECRET",
    user_agent="delta-ghost-ai-sentiment"
)

# Google Trends
pytrends = TrendReq(hl='en-US', tz=360)

# OpenAI Key (if needed for LLM processing)
openai.api_key = "YOUR_OPENAI_API_KEY"

# ========== CUSTOM TECHNICAL FUNCTIONS ==========

def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_ema(series, window=21):
    return series.ewm(span=window, adjust=False).mean()

# ========== SENTIMENT FUNCTIONS ==========

def reddit_sentiment(keyword, limit=50):
    subreddit_list = ['stocks', 'options', 'wallstreetbets']
    sentiment_count = {'positive': 0, 'negative': 0, 'neutral': 0}
    for sub in subreddit_list:
        subreddit = reddit.subreddit(sub)
        for submission in subreddit.search(keyword, limit=limit):
            title = submission.title.lower()
            if 'call' in title or 'bullish' in title:
                sentiment_count['positive'] += 1
            elif 'put' in title or 'bearish' in title:
                sentiment_count['negative'] += 1
            else:
                sentiment_count['neutral'] += 1
    return sentiment_count

def google_trend_score(keyword):
    pytrends.build_payload([keyword], timeframe='now 7-d')
    data = pytrends.interest_over_time()
    if not data.empty:
        return int(data[keyword].iloc[-1])
    return 0

# ========== TRADE SIGNAL LOGIC ==========

def analyze_stock(ticker):
    data = yf.download(ticker, period='3mo', interval='1d')
    data['RSI'] = compute_rsi(data['Close'])
    data['EMA'] = compute_ema(data['Close'])

    latest = data.iloc[-1]
    signal = ""

    if latest['Close'] > latest['EMA'] and latest['RSI'] < 70:
        signal = "Buy Call"
    elif latest['Close'] < latest['EMA'] and latest['RSI'] > 30:
        signal = "Buy Put"
    else:
        signal = "Hold"

    return data, signal

# ========== STREAMLIT FRONT-END ==========

st.title("📈 Delta Ghost AI Analyst")
ticker = st.text_input("Enter Ticker Symbol (e.g., AAPL)", "AAPL")

if st.button("Analyze"):
    data, signal = analyze_stock(ticker)
    trend = google_trend_score(ticker)
    sentiment = reddit_sentiment(ticker)

    st.subheader("📊 Technical Overview")
    st.line_chart(data[['Close', 'EMA']])
    st.write(f"**RSI (Latest):** {data['RSI'].iloc[-1]:.2f}")
    st.write(f"**Signal:** {signal}")

    st.subheader("📢 Sentiment")
    st.write(f"Reddit: {sentiment}")
    st.write(f"Google Trends Score: {trend}")

    st.subheader("📄 Export Report")
    doc = Document()
    doc.add_heading(f"Delta Ghost Trade Report – {ticker}", 0)
    doc.add_paragraph(f"Signal: {signal}")
    doc.add_paragraph(f"RSI: {data['RSI'].iloc[-1]:.2f}")
    doc.add_paragraph(f"Reddit Sentiment: {sentiment}")
    doc.add_paragraph(f"Google Trend Score: {trend}")
    filename = f"{ticker}_trade_report.docx"
    doc.save(filename)

    with open(filename, "rb") as file:
        st.download_button("Download Word Report", file, file_name=filename)

# ========== END ==========
