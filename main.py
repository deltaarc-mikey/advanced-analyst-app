import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import openai
import io
from docx import Document
from streamlit_option_menu import option_menu

# Set up your API keys here
OPENAI_API_KEY = "your_openai_api_key"
UNUSUAL_WHALES_API_KEY = "your_unusual_whales_api_key"
TRADINGVIEW_WEBHOOK_SECRET = "your_webhook_secret"

# Set page config
st.set_page_config(page_title="Delta Ghost AI Trade Engine", layout="wide")

# Sidebar menu
selected = option_menu(
    menu_title=None,
    options=["Screener & Charts", "AI Trade Signal Center", "Options & Uploads"],
    icons=["graph-up-arrow", "cpu", "cloud-upload"],
    orientation="horizontal",
)

# --- Screener & Charts Tab ---
if selected == "Screener & Charts":
    st.title("Step 1: Screener & Technical Charts")
    tickers = st.text_area("Paste top tickers (e.g., NVDA, AMD, VRT):", height=70)
    if st.button("📊 Show Chart"):
        symbols = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        for symbol in symbols:
            url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1=1672531200&period2=1704067200&interval=1d&events=history"
            try:
                df = pd.read_csv(url)
                df['Date'] = pd.to_datetime(df['Date'])
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'],
                                             low=df['Low'], close=df['Close'], name="Price"))
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.error(f"Failed to load chart for {symbol}")

    st.markdown("---")
    st.subheader("📈 Finviz Feed")
    if st.button("Load Finviz RSS"):
        st.info("(RSS Feed parsing coming soon)")

    st.markdown("---")
    st.subheader("🛰️ Unusual Whales Flow")
    ticker = st.text_input("Enter ticker for flow:", value="VRT")
    if st.button("🔍 Get UOA"):
        try:
            response = requests.get(
                f"https://phx.unusualwhales.com/api/historic_chains/{ticker}",
                headers={"Authorization": f"Bearer {UNUSUAL_WHALES_API_KEY}"}
            )
            data = response.json()
            uoa_df = pd.DataFrame(data["chains"][:5])
            st.dataframe(uoa_df)
        except:
            st.error("Failed to load UOA data.")

# --- AI Trade Signal Center Tab ---
elif selected == "AI Trade Signal Center":
    st.title("📡 AI Trade Signal Center")
    st.markdown("Get signals from Gemini + GPT based on uploaded or scanned data.")

    uploaded_file = st.file_uploader("📥 Upload Option Chain CSV")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("Preview of Option Chain:")
        st.dataframe(df.head(10))

        uoa_context = ""
        try:
            uoa_response = requests.get(
                f"https://phx.unusualwhales.com/api/historic_chains/{df['symbol'].iloc[0]}",
                headers={"Authorization": f"Bearer {UNUSUAL_WHALES_API_KEY}"}
            )
            uoa_data = uoa_response.json()
            uoa_df = pd.DataFrame(uoa_data["chains"][:5])
            uoa_context = uoa_df.to_csv(index=False)
            st.dataframe(uoa_df)
        except:
            st.warning("Could not load Unusual Whales data.")

        prompt = f"""
        You are an AI trade analyst. Given the following options chain and unusual options activity (UOA), recommend the highest probability trade setup.

        Options Chain:
        {df.head(10).to_csv(index=False)}

        Unusual Whales Flow:
        {uoa_context}

        Output format:
        - Suggested Trade Type (Call/Put/Spread)
        - Strike, Expiration
        - Reasoning
        - Risk/Reward assessment
        - Suggested Position Size
        """

        if st.button("🧠 Generate AI Trade Plan"):
            openai.api_key = OPENAI_API_KEY
            try:
                result = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                trade_plan = result.choices[0].message.content
                st.text_area("🧾 AI Trade Plan:", trade_plan, height=250)

                # Download as Word doc
                doc = Document()
                doc.add_heading("Delta Ghost AI Trade Plan", 0)
                doc.add_paragraph(trade_plan)
                buffer = io.BytesIO()
                doc.save(buffer)
                st.download_button("📥 Download Trade Plan (Word)", buffer.getvalue(), file_name="trade_plan.docx")
            except Exception as e:
                st.error(f"Failed to generate AI plan: {e}")

# --- Options & Uploads Tab ---
elif selected == "Options & Uploads":
    st.title("📂 Options Chain Upload + TradingView Alerts")

    st.subheader("📤 Upload CSV Chain for Parsing")
    file = st.file_uploader("Choose a CSV option chain:")
    if file:
        try:
            chain_df = pd.read_csv(file)
            st.dataframe(chain_df.head())
        except:
            st.error("Invalid CSV format.")

    st.subheader("📡 TradingView Webhook")
    st.markdown("Set this as your TradingView webhook URL:")
    st.code("https://your-app-name.streamlit.app/webhook?secret=your_webhook_secret", language="text")

    st.info("Webhook receiver will be activated in backend deployment.")
