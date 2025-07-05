import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
import openai
import requests
import feedparser

# ---------------------
# STREAMLIT LAYOUT
# ---------------------
st.set_page_config(layout="wide")
with st.sidebar:
    selected = option_menu(
        menu_title="Delta Ghost AI Trade Engine",
        options=["📊 Screener & Charts", "🤖 AI Trade Signal Center", "⚙️ Options & Uploads"],
        icons=["bar-chart", "cpu", "cloud-upload"],
        menu_icon="graph-up",
        default_index=0,
    )

# ---------------------
# CHARTING TAB
# ---------------------
if selected == "📊 Screener & Charts":
    st.title("Step 1: Screener & Technical Charts")

    tickers_input = st.text_area("Paste top tickers:", "NVDA, AMD, VRT")
    if st.button("📊 Show Chart"):
        tickers = [t.strip().upper() for t in tickers_input.split(",")]
        data = yf.download(tickers, period='6mo')['Adj Close']

        for ticker in tickers:
            if ticker in data.columns:
                df = pd.DataFrame(data[ticker])
                df['SMA20'] = df[ticker].rolling(window=20).mean()
                df['RSI'] = 100 - (100 / (1 + df[ticker].pct_change().rolling(14).mean() / df[ticker].pct_change().rolling(14).std()))

                st.subheader(f"📈 {ticker} - Technical Chart")
                fig, ax = plt.subplots(figsize=(12, 4))
                df[ticker].plot(ax=ax, label='Price')
                df['SMA20'].plot(ax=ax, label='SMA 20')
                ax.set_ylabel("Price (USD)")
                ax.legend()
                st.pyplot(fig)

                st.line_chart(df[['RSI']].dropna(), height=150, use_container_width=True)
            else:
                st.warning(f"No data for {ticker}.")

    # --- Finviz RSS News ---
    st.markdown("---")
    st.header("📉 Finviz Feed")
    if st.button("Load Finviz RSS"):
        rss_url = "https://finviz.com/feed.ashx"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:5]:
            st.markdown(f"**{entry.title}**  \n[{entry.link}]({entry.link})")

    # --- Unusual Whales Integration ---
    st.markdown("---")
    st.header("🛰️ Unusual Whales Flow")
    uw_ticker = st.text_input("Enter ticker for flow:", "VRT")
    if st.button("🐳 Get UOA"):
        UW_API_KEY = st.secrets["UW_API_KEY"]
        url = f"https://unusualwhales.com/api/historic_chains/{uw_ticker}?limit=5"
        headers = {"Authorization": f"Bearer {UW_API_KEY}"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            uw_data = r.json()
            st.json(uw_data)
        else:
            st.error(f"Failed to retrieve UOA: {r.status_code}")

# ---------------------
# AI TRADE SIGNAL CENTER
# ---------------------
elif selected == "🤖 AI Trade Signal Center":
    st.title("🤖 AI Play Comparison: Gemini vs ChatGPT")
    user_prompt = st.text_area("Enter a question or stock setup to analyze:", "Best options trade on NVDA this week?")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧠 ChatGPT")
        if st.button("Run ChatGPT"):
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": user_prompt}]
            )
            gpt_output = response['choices'][0]['message']['content']
            st.write(gpt_output)

    with col2:
        st.subheader("🔮 Gemini")
        if st.button("Run Gemini"):
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"])
            output = llm.invoke(user_prompt)
            st.write(output)

# ---------------------
# OPTIONS & UPLOAD TAB
# ---------------------
elif selected == "⚙️ Options & Uploads":
    st.title("📂 Upload Analyst Files or UOA CSV")
    uploaded_file = st.file_uploader("Upload CSV or document for review", type=["csv", "xlsx", "txt"])
    if uploaded_file is not None:
        st.success("✅ File received!")
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
            st.dataframe(df)
        else:
            content = uploaded_file.read().decode("utf-8")
            st.text(content)
