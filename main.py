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

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.sidebar.title("📊 Delta Ghost AI Trading Panel")
selected_tab = st.sidebar.radio("Navigate", ["Enter Ticker", "Reddit + Trends", "AI Trade Signal Center"])

# --- Load Secrets ---
openai.api_key = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UW_API_KEY = os.getenv("UW_API_KEY")

# --- Reddit Setup ---
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# --- Google Trends ---
pytrends = TrendReq(hl='en-US', tz=360)

# --- Debug: Show Loaded Secrets ---
# st.sidebar.subheader("🔑 Reddit API Debug")
# st.sidebar.write("Client ID:", os.getenv("REDDIT_CLIENT_ID"))
# st.sidebar.write("Client Secret:", os.getenv("REDDIT_CLIENT_SECRET"))
# st.sidebar.write("User Agent:", os.getenv("REDDIT_USER_AGENT"))

# --- Helper: Generate Report ---
def generate_docx(text, filename="Trade_Analysis_Report.docx"):
    doc = Document()
    doc.add_heading("Delta Ghost Trade Report", level=1)
    doc.add_paragraph(text)
    doc.save(filename)
    return filename

# --- Ticker Tab ---
if selected_tab == "Enter Ticker":
    st.title("📈 Enter Ticker Symbol")
    ticker = st.text_input("Enter a stock ticker:", value="AAPL")

    if ticker:
        try:
            data = yf.download(ticker, period="1mo", interval="1d")
            data["RSI"] = yf.Ticker(ticker).history(period="3mo").Close.rolling(window=14).mean()

            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Candlestick'
            ))
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI'))
            fig.update_layout(title=f"{ticker.upper()} - Price + RSI", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig)

            # Unusual Whales API
            st.subheader("📊 Filtered Options Chain (Under $2, Volume > 500)")
            uw_url = f"https://phx.unusualwhales.com/api/historic_chains/{ticker.upper()}"
            headers = {"Authorization": f"Bearer {UW_API_KEY}"}
            response = requests.get(uw_url, headers=headers)

            try:
                chains = response.json()
                if isinstance(chains, list) and len(chains) > 0 and isinstance(chains[0], dict):
                    filtered = [c for c in chains if c.get("ask", 999) < 2 and c.get("volume", 0) > 500]
                    if filtered:
                        df = pd.DataFrame(filtered)
                        st.dataframe(df[["contract_symbol", "type", "strike", "expiration", "ask", "volume"]])
                    else:
                        st.info("No matching options under current filter.")
                else:
                    st.warning("Unusual Whales returned no usable data.")
            except Exception as e:
                st.error(f"Error parsing Unusual Whales response: {e}")

            if datetime.today().weekday() >= 5:
                st.warning("⚠️ The market is currently closed. Data may be stale.")

        except Exception as e:
            st.error(f"Error loading ticker data: {e}")

# --- Reddit + Google Trends Tab ---
elif selected_tab == "Reddit + Trends":
    st.title("📣 Reddit Sentiment + Google Trends")
    keyword = st.text_input("Enter a search keyword:", value="options")

    if keyword:
        try:
            subreddit = reddit.subreddit("options")
            titles = [post.title for post in subreddit.search(keyword, limit=25)]
            st.write("### Reddit Mentions")
            for title in titles:
                st.markdown(f"- {title}")
        except Exception as e:
            st.error(f"Reddit API error: {e}")

        try:
            pytrends.build_payload([keyword], cat=0, timeframe='today 3-m')
            trends = pytrends.interest_over_time()
            if not trends.empty:
                st.line_chart(trends[keyword])
            else:
                st.warning("No Google Trends data found.")
        except Exception as e:
            st.error(f"Google Trends error: {e}")

# --- AI Trade Signal Center ---
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

                docx_path = generate_docx(output)
                file_id = upload_to_drive(docx_path, "Delta_Ghost_Report_ChatGPT.docx")
                st.success(f"Uploaded to Google Drive. File ID: {file_id}")
            except Exception as e:
                st.error(f"OpenAI error: {e}")
