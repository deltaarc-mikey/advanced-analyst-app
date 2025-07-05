import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import openai
from pytrends.request import TrendReq
import praw
from docx import Document

# ----------------------------- CONFIGURATION -----------------------------
openai.api_key = "YOUR_OPENAI_API_KEY"

REDDIT_CLIENT_ID = "YOUR_REDDIT_CLIENT_ID"
REDDIT_SECRET = "YOUR_REDDIT_SECRET"
REDDIT_USER_AGENT = "delta-ghost-ai-sentiment"

# ----------------------------- REDDIT SENTIMENT -----------------------------
def fetch_reddit_sentiment(keyword):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    subreddit = reddit.subreddit("options+wallstreetbets+stocks+Daytrading")
    mentions = 0
    sentiment_score = 0

    for post in subreddit.search(keyword, limit=10):
        mentions += 1
        sentiment_score += post.score

    return mentions, sentiment_score

# ----------------------------- GOOGLE TRENDS -----------------------------
def fetch_google_trends(keyword):
    pytrends = TrendReq()
    pytrends.build_payload([keyword], timeframe="now 7-d")
    df = pytrends.interest_over_time()
    if not df.empty:
        return int(df[keyword].iloc[-1])
    return 0

# ----------------------------- AI SUMMARIZATION -----------------------------
def summarize_with_gpt(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": f"Summarize this stock data and news: {text}"}
        ]
    )
    return response['choices'][0]['message']['content']

# ----------------------------- ANALYSIS LOGIC -----------------------------
def analyze_stock(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="5d")
    info = stock.info
    news = stock.news if hasattr(stock, 'news') else []

    summary_data = f"Stock: {ticker}\n\n"
    summary_data += f"Current Price: {hist['Close'][-1]:.2f}\n"
    summary_data += f"52w High: {info.get('fiftyTwoWeekHigh', 'N/A')}\n"
    summary_data += f"52w Low: {info.get('fiftyTwoWeekLow', 'N/A')}\n"

    if news:
        for item in news[:3]:
            summary_data += f"\nHeadline: {item['title']}\nSummary: {item.get('summary', '')}\n"

    reddit_mentions, reddit_sentiment = fetch_reddit_sentiment(ticker)
    google_trend = fetch_google_trends(ticker)

    summary_data += f"\nReddit Mentions: {reddit_mentions} | Sentiment Score: {reddit_sentiment}"
    summary_data += f"\nGoogle Trend Score: {google_trend}"

    ai_summary = summarize_with_gpt(summary_data)

    return summary_data, ai_summary

# ----------------------------- EXPORT TO WORD -----------------------------
def export_to_word(ticker, summary, ai_summary):
    doc = Document()
    doc.add_heading(f"{ticker} - AI Trade Report", 0)
    doc.add_paragraph("📊 MARKET SUMMARY:\n" + summary)
    doc.add_paragraph("\n🤖 AI SUMMARY:\n" + ai_summary)
    filename = f"{ticker}_report.docx"
    doc.save(filename)
    return filename

# ----------------------------- STREAMLIT UI -----------------------------
st.title("📈 Delta Ghost AI: Smart Trade Reports")
ticker_input = st.text_input("Enter a ticker (e.g., TSLA, AAPL):")

if ticker_input:
    with st.spinner("Analyzing market data and trends..."):
        try:
            summary, ai_summary = analyze_stock(ticker_input.upper())
            st.subheader("📋 Market Snapshot")
            st.text(summary)

            st.subheader("🤖 GPT-4 AI Summary")
            st.write(ai_summary)

            file = export_to_word(ticker_input.upper(), summary, ai_summary)
            with open(file, "rb") as f:
                st.download_button("⬇️ Download Report (.docx)", f, file_name=file)

        except Exception as e:
            st.error(f"❌ Error: {e}")
