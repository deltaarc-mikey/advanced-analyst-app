import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import io
import pandas as pd
import contextlib
from googleapiclient.discovery import build

plt.switch_backend('agg')

# --- Tool Definitions ---

def generate_price_chart(tickers_string):
    """
    Generates a chart and returns a success message.
    The chart image itself is stored in the session state for the UI to display.
    """
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
    
    # --- THIS IS THE CHANGE ---
    # Store the image buffer in session state instead of returning it
    st.session_state.last_chart = buf
    # Return a simple success message to the agent
    return f"Chart for {', '.join(price_data.columns)} was generated successfully."
    # --- END OF CHANGE ---

def Google_Search_for_news(query):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        cse_id = st.secrets["GOOGLE_CSE_ID"]
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=5).execute()
        if 'items' in res:
            formatted_results = []
            for item in res['items']:
                title = item.get('title', 'No Title')
                link = item.get('link', '#')
                snippet = item.get('snippet', 'No snippet available.').replace('\n', '')
                formatted_results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n---")
            return "\n".join(formatted_results)
        else: return f"No search results found for '{query}'."
    except Exception as e: return f"An error occurred during the search: {e}"

# --- Agent and UI Setup ---
st.set_page_config(layout="wide")
st.title("📈 Advanced AI Analyst")
st.write("This AI can generate charts and search the web for the latest news.")

if 'agent_executor' not in st.session_state:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import Tool, AgentExecutor, create_react_agent
    from langchain import hub
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"])
    tools = [
        Tool(name="generate_price_chart", func=generate_price_chart, description="Use to create a stock price comparison chart. Input is a string of tickers like 'AAPL,MSFT'."),
        Tool(name="Google_Search_for_news", func=Google_Search_for_news, description="Use to search for recent news on a company or topic. Input is a search query string.")
    ]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    st.session_state.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- UI Interaction ---
st.header("Ask me anything:")
user_question = st.text_input("Examples: 'Chart the price of TSLA,RIVN,LCID' or 'What is the latest news on Vertiv Holdings?'", "")

if user_question:
    st.session_state.last_chart = None # Reset chart state on new question
    with st.spinner("Thinking..."):
        string_io = io.StringIO()
        with contextlib.redirect_stdout(string_io):
             response = st.session_state.agent_executor.invoke({"input": user_question})
        thought_process = string_io.getvalue()
        
        output = response.get("output")
        
        # --- THIS IS THE CHANGE ---
        st.markdown("### Final Answer:")
        # Check if the chart tool stored an image in the session state
        if st.session_state.last_chart:
            st.image(st.session_state.last_chart)
            # Optionally, display the success message the agent saw
            st.write(output)
        else:
            # Otherwise, just display the text output from the agent
            st.write(output)
        # --- END OF CHANGE ---

        with st.expander("Show Thought Process"):
            st.text(thought_process)
