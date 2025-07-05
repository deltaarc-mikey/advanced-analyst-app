import streamlit as st
import pandas as pd
import json
import openai

st.set_page_config(page_title="Delta Ghost AI Trade Engine", layout="wide")

st.title("Delta Ghost AI Trade Engine")
st.caption("Built with Gemini + ChatGPT + Unusual Whales Intelligence")

# --- Tabs ---
tabs = st.tabs(["Screener & Charts", "AI Trade Signal Center", "Options & Uploads"])

# --- Tab 1: Screener & TradingView Alerts ---
with tabs[0]:
    st.header("Step 1: Screener & Technical Charts")
    tickers = st.text_area("Paste top tickers (e.g., NVDA, AMD, VRT):", height=50)
    if st.button("Show Chart"):
        st.info(f"Tickers entered: {tickers}")

    st.markdown("---")
    st.subheader("TradingView Alert Parser")
    alert_payload = st.text_area("Paste TradingView Webhook JSON alert:", height=200)
    if st.button("Parse Alert"):
        try:
            data = json.loads(alert_payload)
            st.success("Alert parsed successfully!")
            st.json(data)
        except json.JSONDecodeError:
            st.error("Invalid JSON format. Please check the structure.")

# --- Tab 2: AI Trade Planner ---
with tabs[1]:
    st.header("AI Trade Plan Generator")

    ticker = st.text_input("Enter Ticker:", value="AAPL")
    uoa_notes = st.text_area("Paste Unusual Whales Summary:")
    gemini_notes = st.text_area("Paste Gemini Notes:")

    if st.button("Generate AI Trade Plan"):
        if not (uoa_notes or gemini_notes):
            st.warning("Please enter at least UOA or Gemini notes.")
        else:
            prompt = f"""
Generate an options trade plan for {ticker} using the following data:

Unusual Whales Flow:
{uoa_notes}

Gemini Strategy:
{gemini_notes}

Please recommend:
1. Option type (call/put/spread)
2. Strike prices & expiry
3. Capital usage
4. Risk/reward summary
5. Execution instructions
"""
            try:
                openai.api_key = st.secrets["OPENAI_API_KEY"]
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.subheader("AI Trade Plan")
                st.markdown(response.choices[0].message["content"])
            except Exception as e:
                st.error(f"OpenAI Error: {e}")

# --- Tab 3: Upload Option Chain ---
with tabs[2]:
    st.header("Upload Option Chain File")

    uploaded_file = st.file_uploader("Upload your Option Chain (CSV or Excel):", type=["csv", "xlsx"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.success("File uploaded successfully!")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"File error: {e}")
