import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import io
import contextlib
import feedparser
import requests
from googleapiclient.discovery import build
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor, create_react_agent, hub
from tastytrade import TastySession
from tastytrade.orders import EquityOrder, OrderAction, OrderType, TimeInForce
from tastytrade.instruments import Equity
from docx import Document
from fpdf import FPDF
from datetime import datetime

plt.switch_backend('agg')
st.set_page_config(layout="wide")
st.title("📊 Advanced AI Trading Dashboard")

# --- Functions ---
def generate_price_chart(ticker):
    data = yf.download(ticker, period="6mo")
    if data.empty:
        return "No data found."
    data['RSI'] = ta.rsi(data['Close'], length=14)
    data['SMA50'] = ta.sma(data['Close'], length=50)
    data.dropna(inplace=True)

    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(data.index, data['Close'], label='Close Price')
    ax.plot(data.index, data['SMA50'], label='SMA 50')
    ax2 = ax.twinx()
    ax2.plot(data.index, data['RSI'], label='RSI', color='purple', alpha=0.4)
    ax.set_title(f"{ticker} Price Chart with RSI and SMA")
    ax.legend(loc='upper left')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def tasty_login():
    try:
        return TastySession(
            username=st.secrets["TASTYTRADE_USERNAME"],
            password=st.secrets["TASTYTRADE_PASSWORD"]
        )
    except Exception as e:
        st.error(f"Login failed: {e}")
        return None

def place_order(session, symbol, quantity, order_type='MARKET', limit_price=None):
    try:
        instrument = Equity(symbol)
        order = EquityOrder(
            session=session,
            action=OrderAction.BUY_TO_OPEN,
            time_in_force=TimeInForce.DAY,
            order_type=OrderType.MARKET if order_type == 'MARKET' else OrderType.LIMIT,
            price=limit_price,
            quantity=quantity,
            instrument=instrument
        )
        order.send()
        return f"✅ Order sent for {symbol} x{quantity} ({order_type})"
    except Exception as e:
        return f"❌ Order failed: {e}"

def generate_trade_doc(trade_summary):
    doc = Document()
    doc.add_heading('AI Trade Report', 0)
    doc.add_paragraph(trade_summary)
    filename = f"AI_Trade_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
    doc.save(filename)
    return filename

def generate_trade_pdf(trade_summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, trade_summary)
    filename = f"AI_Trade_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    pdf.output(filename)
    return filename

def Gemini_Search(query):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        cse_id = st.secrets["GOOGLE_CSE_ID"]
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=5).execute()
        results = []
        for item in res.get('items', []):
            results.append(f"{item['title']}\n{item['link']}\n{item['snippet']}\n")
        return '\n---\n'.join(results)
    except Exception as e:
        return f"Error with Gemini search: {e}"

# --- Tabs ---
tabs = st.tabs(["📈 Chart", "🤖 AI Trade Center", "📤 Auto Execution"])

with tabs[0]:
    st.header("Chart + Indicators")
    ticker_input = st.text_input("Enter a ticker", "AAPL")
    if st.button("Generate Chart"):
        chart = generate_price_chart(ticker_input)
        if isinstance(chart, str): st.error(chart)
        else: st.image(chart)

with tabs[1]:
    st.header("ChatGPT & Gemini Signal Center")
    query = st.text_input("Enter topic or stock for Gemini signal", "NVDA AI chips")
    if st.button("Run Gemini Search"):
        result = Gemini_Search(query)
        st.text_area("Gemini Results", result, height=300)
        doc_file = generate_trade_doc(result)
        pdf_file = generate_trade_pdf(result)
        with open(doc_file, 'rb') as f:
            st.download_button("Download Word Report", f, file_name=doc_file)
        with open(pdf_file, 'rb') as f:
            st.download_button("Download PDF Report", f, file_name=pdf_file)

with tabs[2]:
    st.header("Live Trade Execution")
    symbol = st.text_input("Symbol", "TSLA")
    qty = st.number_input("Quantity", min_value=1, value=1)
    order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
    limit_price = None
    if order_type == "LIMIT":
        limit_price = st.number_input("Limit Price", min_value=0.01, value=1.00, step=0.01)
    if st.button("Execute via TastyTrade"):
        session = tasty_login()
        if session:
            res = place_order(session, symbol, qty, order_type, limit_price)
            st.success(res)
        else:
            st.error("Could not log in.")
