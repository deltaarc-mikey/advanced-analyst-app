import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import praw
from pytrends.request import TrendReq
from docx import Document
from datetime import datetime
import openai

# ========== CONFIGURATION ==========

REDDIT_CLIENT_ID = "YOUR_REDDIT_CLIENT_ID"
REDDIT_CLIENT_SECRET = "YOUR_REDDIT_CLIENT_SECRET"
REDDIT_USER_AGENT = "delta-ghost-ai-sentiment"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

openai.api_key = OPENAI_API_KEY

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

pytrends = TrendReq(hl='en-US', tz=360)

# ========== HELPER FUNCTIONS ==========

def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_ema(series, window=21):
    return series.ewm(span=window, adjust=False).mean()

def reddit_sentiment(keyword, limit=50):
    subs = ['stocks', 'options', 'wallstreetbets']
    sentiment = {'positive': 0, 'negative': 0, 'neutral': 0}
    for sub in subs:
        for post in reddit.subreddit(sub).search(keyword, limit=limit):
            title = post.title.lower()
            if "call" in title or "bullish" in title:
                sentiment["positive"] += 1
            elif "put" in title or "bearish" in title:
                sentiment["negative"] += 1
            else:
                sentiment["neutral"] += 1
    return sentiment

def google_trend_score(keyword):
    pytrends.build_payload([keyword], timeframe='now 7-d')
    data = pytrends.interest_over_time()
    if not data.empty:
        return int(data[keyword].iloc[-1])
    return 0

def analyze_stock(ticker):
    df = yf.download(ticker, period='3mo', interval='1d')
    df['RSI'] = compute_rsi(df['Close'])
    df['EMA'] = compute_ema(df['Close'])
    last = df.iloc[-1]
    if last['Close'] > last['EMA'] and last['RSI'] < 70:
        return df, "Buy Call"
    elif last['Close'] < last['EMA'] and last['RSI'] > 30:
        return df, "Buy Put"
    else:
        return df, "Hold"

def generate_llm_summary(ticker, signal, rsi, sentiment, trend):
    prompt = f"""
    Provide a concise, professional summary for a stock trading signal:
    Ticker: {ticker}
    Signal: {signal}
    RSI: {rsi}
    Reddit Sentiment: {sentiment}
    Google Trends Score: {trend}
    Summary should be clear and actionable.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

# ========== STREAMLIT UI ==========

st.set_page_config(page_title="Delta Ghost LLM Analyst", layout="centered")
st.title("📈 Delta Ghost AI Trade Report")

ticker = st.text_input("Enter Ticker Symbol (e.g., TSLA)", "AAPL")

if st.button("Run Full Analysis"):
    with st.spinner("Analyzing trade setup..."):
        df, signal = analyze_stock(ticker)
        rsi = df['RSI'].iloc[-1]
        trend_score = google_trend_score(ticker)
        sentiment = reddit_sentiment(ticker)

        st.subheader("📊 Technical Indicators")
        st.line_chart(df[['Close', 'EMA']])
        st.write(f"**Latest RSI:** {rsi:.2f}")
        st.write(f"**Signal:** {signal}")

        st.subheader("📢 Sentiment Snapshot")
        st.write(f"**Reddit:** {sentiment}")
        st.write(f"**Google Trends Score:** {trend_score}")

        st.subheader("🧠 GPT-4 Summary")
        summary = generate_llm_summary(ticker, signal, rsi, sentiment, trend_score)
        st.info(summary)

        doc = Document()
        doc.add_heading(f"{ticker} – AI Trade Report", 0)
        doc.add_paragraph(f"Signal: {signal}")
        doc.add_paragraph(f"RSI: {rsi:.2f}")
        doc.add_paragraph(f"Reddit Sentiment: {sentiment}")
        doc.add_paragraph(f"Google Trends Score: {trend_score}")
        doc.add_paragraph(f"\nLLM Summary:\n{summary}")
        filename = f"{ticker}_trade_report.docx"
        doc.save(filename)

        with open(filename, "rb") as f:
            st.download_button("📄 Download Word Report", f, file_name=filename)
