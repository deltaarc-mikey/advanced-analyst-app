import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import io
import pandas as pd
import contextlib
from googleapiclient.discovery import build
import traceback

plt.switch_backend('agg')

# --- Tool Functions ---

def generate_price_chart(tickers_string):
    """Directly generates a price chart."""
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
    if not tickers: return "No tickers provided."
    raw_data = yf.download(tickers, period='1y', progress=False)
    if raw_data.empty: return f"Could not find any data for the tickers: {', '.join(tickers)}."

    if 'Adj Close' in raw_data.columns:
        price_data, price_label = raw_data['Adj Close'], 'Adjusted Close Price'
    elif 'Close' in raw_data.columns:
        price_data, price_label = raw_data['Close'], 'Close Price'
    else: return "Could not find 'Adj Close' or 'Close' columns."

    if isinstance(price_data, pd.Series): price_data = price_data.to_frame(name=tickers[0])
    price_data.dropna(axis=1, how='all', inplace=True)
    if price_data.empty: return f"All tickers provided were invalid or had no data: {', '.join(tickers)}."

    fig, ax = plt.subplots(figsize=(12, 7))
    price_data.plot(ax=ax)
    ax.set_title('Stock Price Comparison (Last Year)', fontsize=16)
    ax.set_ylabel(f'{price_label} (USD)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.grid(True)
    ax.legend(title='Tickers')

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

def Google_Search_for_news(query):
    """This function is used by the AI agent."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        cse_id = st.secrets["GOOGLE_CSE_ID"]
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

# --- Streamlit User Interface ---
st.set_page_config(layout="wide")
st.title("📈 Advanced AI Analyst")

# --- Section 1: Charting Tool (No AI) ---
st.header("Comparative Price Chart")
chart_ticker_input = st.text_input("Enter stock tickers separated by commas:", "AAPL,MSFT,NVDA", key="chart_input")
if st.button("Generate Chart"):
    if chart_ticker_input:
        with st.spinner("Generating chart..."):
            result = generate_price_chart(chart_ticker_input)
            if isinstance(result, str): st.error(result)
            else: st.image(result)
    else:
        st.warning("Please enter at least one ticker for the chart.")

st.markdown("---")

# --- Section 2: AI Research Assistant ---
st.header("🤖 AI Research Assistant")

if 'agent_executor' not in st.session_state:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"])
    tools = [Tool(name="Google_Search_for_news", func=Google_Search_for_news, description="Use to search for recent news on a company or topic.")]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    st.session_state.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- UI Interaction ---
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
    else:
        st.warning("Please enter a question for the AI.")
