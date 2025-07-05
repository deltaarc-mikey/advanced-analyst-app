import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import io
import pandas as pd
import numpy as np
import contextlib
from googleapiclient.discovery import build
import traceback

plt.switch_backend('agg')

# --- Tool Functions ---

def generate_price_chart(tickers_string):
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
    if not tickers: return "No tickers provided."
    raw_data = yf.download(tickers, period='1y', progress=False)
    if raw_data.empty: return f"Could not find any data for the tickers: {', '.join(tickers)}."

    if 'Adj Close' in raw_data.columns: price_data, price_label = raw_data['Adj Close'], 'Adjusted Close Price'
    elif 'Close' in raw_data.columns: price_data, price_label = raw_data['Close'], 'Close Price'
    else: return "Could not find 'Adj Close' or 'Close' columns."

    if isinstance(price_data, pd.Series): price_data = price_data.to_frame(name=tickers[0])
    price_data.dropna(axis=1, how='all', inplace=True)
    if price_data.empty: return f"All tickers provided were invalid or had no data: {', '.join(tickers)}."

    fig, ax = plt.subplots(figsize=(12, 7)); price_data.plot(ax=ax)
    ax.set_title('Stock Price Comparison (Last Year)', fontsize=16); ax.set_ylabel(f'{price_label} (USD)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12); ax.grid(True); ax.legend(title='Tickers')
    buf = io.BytesIO(); fig.savefig(buf, format='png'); buf.seek(0); plt.close(fig)
    return buf

def Google_Search_for_news(query):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]; cse_id = st.secrets["GOOGLE_CSE_ID"]
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=5).execute()
        if 'items' in res:
            formatted_results = []
            for item in res['items']:
                title = item.get('title', 'No Title'); link = item.get('link', '#'); snippet = item.get('snippet', 'No snippet available.').replace('\n', '')
                formatted_results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n---")
            return "\n".join(formatted_results)
        else: return f"No search results found for '{query}'."
    except Exception as e: return f"An error occurred during the search: {e}"

def generate_technical_heatmap(tickers_string):
    """Generates a heatmap using a simpler, more robust method."""
    try:
        tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
        if not tickers: return "No tickers provided."
        results = []
        for ticker in tickers:
            data = yf.download(ticker, period='4mo', progress=False, auto_adjust=True)
            if data.empty or len(data) < 52: continue
            delta = data['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean(); rs = gain / loss.replace(0, 1e-10) 
            data['RSI'] = 100 - (100 / (1 + rs))
            data['SMA20'] = data['Close'].rolling(window=20).mean(); data['SMA50'] = data['Close'].rolling(window=50).mean()
            latest = data.dropna().iloc[-1]; last_two_sma20 = data['SMA20'].dropna().iloc[-2:]
            if len(last_two_sma20) == 2:
                results.append({
                    'Ticker': ticker, 'RSI': f"{latest['RSI']:.1f}",
                    'Above_SMA50': 'Yes' if latest['Close'] > latest['SMA50'] else 'No',
                    'SMA20_Slope': 'Up' if last_two_sma20.iloc[1] > last_two_sma20.iloc[0] else 'Down'
                })
        if not results: return "Could not generate heatmap for any of the given tickers."
        indicator_df = pd.DataFrame(results).set_index('Ticker')

        # --- Simpler and Corrected Plotting Logic ---
        fig, ax = plt.subplots(figsize=(8, len(indicator_df) * 0.5)); ax.axis('tight'); ax.axis('off')
        table = ax.table(cellText=indicator_df.values, colLabels=indicator_df.columns, rowLabels=indicator_df.index, loc='center', cellLoc='center')

        # Loop through cells to set colors individually
        for i in range(len(indicator_df)):
            # RSI Column (0)
            rsi_val = float(indicator_df.values[i, 0])
            if rsi_val > 70: color = 'mistyrose' # Overbought
            elif rsi_val < 30: color = 'lightgreen' # Oversold
            else: color = 'white'
            table[i+1, 0].set_facecolor(color)

            # Above_SMA50 Column (1)
            color = 'lightgreen' if indicator_df.values[i, 1] == 'Yes' else 'mistyrose'
            table[i+1, 1].set_facecolor(color)

            # SMA20_Slope Column (2)
            color = 'lightgreen' if indicator_df.values[i, 2] == 'Up' else 'mistyrose'
            table[i+1, 2].set_facecolor(color)

        table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1.2, 1.8)
        buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        buf.seek(0); plt.close(fig)
        return buf
    except Exception as e:
        return f"A critical error occurred: {e}\n\nTraceback:\n{traceback.format_exc()}"

# --- Streamlit User Interface ---
st.set_page_config(layout="wide"); st.title("📈 Advanced AI Analyst")
st.header("Comparative Price Chart")
chart_ticker_input = st.text_input("Enter stock tickers separated by commas:", "AAPL,MSFT,NVDA", key="chart_input")
if st.button("Generate Chart"):
    if chart_ticker_input:
        with st.spinner("Generating chart..."):
            result = generate_price_chart(chart_ticker_input)
            if isinstance(result, str): st.error(result)
            else: st.image(result)
st.markdown("---")
st.header("📊 Technical Indicators Heatmap")
heatmap_ticker_input = st.text_input("Enter stock tickers for the heatmap:", "TSLA,GOOG,NVDA,VRT,FDX,HIMS", key="heatmap_input")
if st.button("Generate Heatmap"):
    if heatmap_ticker_input:
        with st.spinner("Generating heatmap..."):
            result = generate_technical_heatmap(heatmap_ticker_input)
            if isinstance(result, str): st.error(result)
            else: st.image(result)
st.markdown("---")
st.header("🤖 AI Research Assistant")
if 'agent_executor' not in st.session_state:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import Tool, AgentExecutor, create_react_agent
    from langchain import hub
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"])
    tools = [Tool(name="Google_Search_for_news", func=Google_Search_for_news, description="Use to search for recent news on a company or topic.")]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    st.session_state.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
ai_question = st.text_input("Ask for news or recent developments:", "Latest news on AI infrastructure stocks", key="ai_input")
if st.button("Ask AI"):
    if ai_question:
        with st.spinner("AI is searching..."):
            string_io = io.StringIO()
            with contextlib.redirect_stdout(string_io):
                 response = st.session_state.agent_executor.invoke({"input": ai_question})
            thought_process = string_io.getvalue()
            output = response.get("output")
            st.markdown("### AI Response:"); st.write(output)
            with st.expander("Show Thought Process"): st.text(thought_process)
