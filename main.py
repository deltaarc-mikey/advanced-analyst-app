# main.py
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import requests
import praw
from pytrends.request import TrendReq
from docx import Document
import yfinance as yf
import openai
import os
from datetime import datetime
import os
import streamlit as st
import praw

# DEBUG: Show if secrets are loaded
st.sidebar.subheader("🔑 Reddit API Debug")
st.sidebar.write("Client ID:", os.getenv("REDDIT_CLIENT_ID"))
st.sidebar.write("Client Secret:", os.getenv("REDDIT_CLIENT_SECRET"))
st.sidebar.write("User Agent:", os.getenv("REDDIT_USER_AGENT"))

# ✅ Reddit API connection
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# --- Sidebar ---
st.set_page_config(layout="wide")
st.sidebar.title("📊 Delta Ghost AI Trading Panel")
selected_tab = st.sidebar.radio("Navigate", ["Enter Ticker", "Reddit + Trends", "AI Trade Signal Center"])

# --- Reddit + Google Trends Config ---
reddit = praw.Reddit(
    client_id=os.getenv("reddit_client_id"),
    client_secret=os.getenv("reddit_client_secret"),
    user_agent=os.getenv("reddit_user_agent")
)
pytrends = TrendReq(hl='en-US', tz=360)

# --- OpenAI and Gemini Config ---
openai.api_key = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Unusual Whales API ---
UW_API_KEY = os.getenv("UW_API_KEY")

# --- Helper: Format Trade Summary ---
def generate_docx(text, filename="Trade_Analysis_Report.docx"):
    doc = Document()
    doc.add_heading("Delta Ghost Trade Report", level=1)
    doc.add_paragraph(text)
    doc.save(filename)
    return filename

# --- Main Tab ---
if selected_tab == "Enter Ticker":
    st.title("📈 Enter Ticker Symbol")
    ticker = st.text_input("Enter a stock ticker:", value="AAPL")

    if ticker:
        try:
            # Pull Yahoo Finance data
            data = yf.download(ticker, period="1mo", interval="1d")
            data["RSI"] = yf.Ticker(ticker).history(period="3mo").Close.rolling(window=14).mean()

            # Plot
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Candlestick'))
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI'))
            fig.update_layout(title=f"{ticker} - Price + RSI", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig)

            # Unusual Whales options chain
            st.subheader("📊 Filtered Options Chain (Under $2, Volume > 500)")
            uw_url = f"https://phx.unusualwhales.com/api/historic_chains/{ticker.upper()}"
            headers = {"Authorization": f"Bearer {UW_API_KEY}"}
            response = requests.get(uw_url, headers=headers)
            if response.status_code == 200:
                chains = response.json()
                filtered = [c for c in chains if c.get("ask", 999) < 2 and c.get("volume", 0) > 500]
                if filtered:
                    df = pd.DataFrame(filtered)
                    st.dataframe(df[["contract_symbol", "type", "strike", "expiration", "ask", "volume"]])
                else:
                    st.info("No matching options under current filter.")
            else:
                st.error("Failed to fetch options from Unusual Whales.")

            if datetime.today().weekday() >= 5:
                st.warning("⚠️ The market is currently closed. Data may be stale.")

        except Exception as e:
            st.error(f"Error loading ticker data: {e}")

# --- Reddit + Google Trends Tab ---
elif selected_tab == "Reddit + Trends":
    st.title("📣 Reddit Sentiment + Google Trends")
    keyword = st.text_input("Enter a search keyword:", value="options")
    if keyword:
        # Reddit scrape
        subreddit = reddit.subreddit("options")
        titles = [post.title for post in subreddit.hot(limit=25)]
        st.write("### Reddit Mentions")
        for title in titles:
            st.markdown(f"- {title}")

        # Google Trends
        pytrends.build_payload([keyword], cat=0, timeframe='today 3-m')
        trends = pytrends.interest_over_time()
        if not trends.empty:
            st.line_chart(trends[keyword])
        else:
            st.warning("No Google Trends data found.")

# --- AI Signal Center ---
elif selected_tab == "AI Trade Signal Center":
    st.title("🤖 AI Trade Signal Center")
    gemini_input = st.text_area("Enter summary or paste data for Gemini:")
    gpt_input = st.text_area("Enter summary or paste data for ChatGPT:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Run Gemini Analysis"):
            try:
                gemini_response = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                    headers={"Content-Type": "application/json"},
                    params={"key": GEMINI_API_KEY},
                    json={"contents": [{"parts": [{"text": gemini_input}]}]}
                )
                result = gemini_response.json()['candidates'][0]['content']['parts'][0]['text']
                st.subheader("Gemini Output")
                st.write(result)
            except Exception as e:
                st.error(f"Gemini error: {e}")

    with col2:
        if st.button("Run ChatGPT Analysis"):
            try:
                chat_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a professional financial analyst."},
                        {"role": "user", "content": gpt_input},
                    ]
                )
                output = chat_response['choices'][0]['message']['content']
                st.subheader("ChatGPT Output")
                st.write(output)
            except Exception as e:
                st.error(f"OpenAI error: {e}")
