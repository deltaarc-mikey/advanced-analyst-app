import os
import json
import requests
import streamlit as st
import yfinance as yf
from pytrends.request import TrendReq
from dotenv import load_dotenv
import praw
from fastapi import FastAPI, Request

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# ---------- Streamlit UI ----------
st.set_page_config(page_title="📈 Delta Ghost AI", layout="wide")
st.title("📈 Delta Ghost AI: Smart Trade Reports")
ticker = st.text_input("Enter a ticker (e.g., TSLA, AAPL):")

# ---------- Data Gathering ----------
def get_yf_summary(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return f"{info.get('shortName', '')} ({ticker.upper()}): {info.get('longBusinessSummary', 'No summary available.')}"
    except Exception as e:
        return f"Error fetching stock data: {e}"

def get_reddit_sentiment(ticker):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        posts = reddit.subreddit("wallstreetbets").search(ticker, limit=5)
        sentiments = [f"📌 {post.title}" for post in posts]
        return "\n".join(sentiments) if sentiments else "No Reddit mentions found."
    except Exception as e:
        return f"Reddit error: {e}"

def get_google_trends(ticker):
    try:
        pytrends = TrendReq()
        pytrends.build_payload([ticker], timeframe='now 7-d')
        df = pytrends.interest_over_time()
        if df.empty:
            return "No Google Trends data."
        score = df[ticker].iloc[-1]
        return f"Google Trends score (latest): {score}"
    except Exception as e:
        return f"Google Trends error: {e}"

# ---------- AI Summaries ----------
def get_chatgpt_summary(prompt):
    if not OPENAI_API_KEY:
        return "❌ OpenAI key missing."
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}]
        }
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ChatGPT error: {e}"

def get_gemini_summary(prompt):
    if not GEMINI_API_KEY:
        return "❌ Gemini key missing."
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        params = {"key": GEMINI_API_KEY}
        res = requests.post(url, headers=headers, params=params, json=payload)
        res.raise_for_status()
        return res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini error: {e}"

# ---------- Webhook Endpoint ----------
app = FastAPI()

@app.post("/webhook")
async def tradingview_webhook(req: Request):
    data = await req.json()
    print("📡 Webhook received:", data)
    # You can log or route this into a file/database/LLM/etc.
    return {"status": "Webhook received"}

# ---------- Execute Workflow ----------
if ticker:
    st.markdown("---")
    st.subheader(f"🧠 Analyzing: {ticker.upper()}")

    yf_summary = get_yf_summary(ticker)
    reddit_sentiment = get_reddit_sentiment(ticker)
    google_score = get_google_trends(ticker)

    prompt = f"""Analyze the following information about {ticker.upper()} for potential stock or options trade opportunities:
    
    Stock Summary:
    {yf_summary}

    Reddit Sentiment:
    {reddit_sentiment}

    Google Trends:
    {google_score}
    """

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💬 ChatGPT Summary")
        st.info(get_chatgpt_summary(prompt))

    with col2:
        st.markdown("### 🌐 Gemini Summary")
        st.success(get_gemini_summary(prompt))

    with st.expander("📊 Raw Data"):
        st.markdown(f"**Stock Summary:**\n\n{yf_summary}")
        st.markdown(f"**Reddit Mentions:**\n\n{reddit_sentiment}")
        st.markdown(f"**Google Trends:**\n\n{google_score}")
