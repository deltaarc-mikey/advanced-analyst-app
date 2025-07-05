import streamlit as st
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from docx import Document
from fpdf import FPDF
from datetime import datetime
import requests
import json
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain import hub
from tastytrade.session import TastySession  # Updated import
from tastytrade.order import Order
from tastytrade.instruments import get_instruments
from tastytrade.utils import pretty_json

# --- App Title ---
st.set_page_config(page_title="Delta Ghost AI Trade Engine", layout="wide")
st.title("Delta Ghost AI Trade Engine")
st.caption("Built with Gemini + ChatGPT + Unusual Whales Intelligence")

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Screener & Charts", "AI Trade Signal Center", "Options & Uploads"])

# --- Shared Session State ---
if "gemini_signals" not in st.session_state:
    st.session_state["gemini_signals"] = []

# --- Helper Functions ---
def generate_word_report(content, filename):
    doc = Document()
    doc.add_heading("Delta Ghost Trade Report", 0)
    for paragraph in content:
        doc.add_paragraph(paragraph)
    doc.save(filename)
    return filename

def generate_pdf_report(content, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Delta Ghost AI Trade Report", ln=True, align='C')
    for line in content:
        pdf.cell(200, 10, txt=line, ln=True, align='L')
    pdf.output(filename)
    return filename

def parse_options_file(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df

def schedule_gemini_pull():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.success(f"✅ Gemini signal pulled at {now}")
    # Placeholder logic
    st.session_state["gemini_signals"].append({"time": now, "signal": "AAPL breakout @ 210+ expected"})

def handle_webhook():
    st.info("Webhook Received! Processing TradingView Alert...")
    # Insert logic here to parse TradingView alert JSON and act accordingly

def tastytrade_execute_trade(symbol, action, quantity, order_type="Limit"):
    try:
        session = TastySession("your_email", "your_password")
        instruments = get_instruments(session, symbol=symbol, instrument_type="Equity Option")
        # Example only: You need to filter specific options chain for strike, expiry, etc.
        order = Order(session, action=action, symbol=symbol, quantity=quantity, order_type=order_type)
        result = order.place()
        st.success(f"Trade Executed: {pretty_json(result)}")
    except Exception as e:
        st.error(f"❌ Trade Failed: {e}")

# --- Screener & Charts Page ---
if menu == "Screener & Charts":
    st.subheader("Step 1: Screener & Technical Charts")
    tickers = st.text_area("Paste top tickers (e.g., NVDA, AMD, VRT):", height=100)
    if tickers:
        tickers_list = [t.strip().upper() for t in tickers.split(",")]
        st.write("You entered:", tickers_list)
        # Placeholder for actual charting or TA engine

# --- AI Trade Signal Center ---
elif menu == "AI Trade Signal Center":
    st.subheader("Step 2: Auto-Generated AI Trade Plans")
    if st.button("Schedule Gemini Pull"):
        schedule_gemini_pull()

    if st.session_state["gemini_signals"]:
        for sig in st.session_state["gemini_signals"]:
            st.info(f"🧠 Gemini Signal @ {sig['time']} — {sig['signal']}")

    export_option = st.selectbox("Export Report Format", ["Word", "PDF"])
    if st.button("Generate Trade Report"):
        sample_report = ["Signal: AAPL bullish breakout expected", "Entry target: $210", "Exit target: $225"]
        if export_option == "Word":
            filename = generate_word_report(sample_report, "delta_ghost_trade_report.docx")
            with open(filename, "rb") as f:
                st.download_button("📥 Download Word Report", f, file_name=filename)
        else:
            filename = generate_pdf_report(sample_report, "delta_ghost_trade_report.pdf")
            with open(filename, "rb") as f:
                st.download_button("📥 Download PDF Report", f, file_name=filename)

# --- Options Chain Upload Page ---
elif menu == "Options & Uploads":
    st.subheader("Step 3: Upload Option Chains or Setup Webhooks")
    uploaded_file = st.file_uploader("Upload Options CSV", type="csv")
    if uploaded_file:
        df = parse_options_file(uploaded_file)
        st.dataframe(df.head())
        st.success("File parsed successfully. Displaying top rows.")

    st.subheader("TradingView Webhook Listener")
    if st.button("Simulate Webhook Alert"):
        handle_webhook()
