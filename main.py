import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import io
import pandas as pd
import contextlib
from googleapiclient.discovery import build

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

# vvv UPDATED HEATMAP FUNCTION vvv
def generate_technical_heatmap(tickers_string):
    """Generates a heatmap of key technical indicators with robust error handling."""
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
    if not tickers: return "No tickers provided."

    indicator_df = pd.DataFrame(index=tickers, columns=['RSI', 'Above_SMA50', 'SMA20_Slope'])

    for ticker in tickers:
        try:
            data = yf.download(ticker, period='4mo', progress=False, auto_adjust=True)
            if data.empty or len(data) < 51: continue # Ensure enough data for 50-day SMA

            # --- More Robust Indicator Calculations ---
            # RSI Calculation
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            # Avoid division by zero for RSI
            rs = gain / loss.replace(0, 1e-10) 
            rsi = 100 - (100 / (1 + rs))
            
            # SMA Calculation
            sma20 = data['Close'].rolling(window=20).mean()
            sma50 = data['Close'].rolling(window=50).mean()

            # Get latest values safely
            latest_close = data['Close'].iloc[-1]
            rsi_val = rsi.iloc[-1]
            sma50_val = sma50.iloc[-1]
            sma20_val = sma20.iloc[-1]
            prev_sma20_val = sma20.iloc[-2]

            # Assign to DataFrame only if all values are valid
            if all(pd.notna(v) for v in [rsi_val, sma50_val, sma20_val, prev_sma20_val]):
                indicator_df.loc[ticker, 'RSI'] = rsi_val
                indicator_df.loc[ticker, 'Above_SMA50'] = 'Yes' if latest_close > sma50_val else 'No'
                indicator_df.loc[ticker, 'SMA20_Slope'] = 'Up' if sma20_val > prev_sma20_val else 'Down'
            # --- End of robust calculations ---

        except Exception:
            continue
    
    indicator_df.dropna(how='all', inplace=True)
    if indicator_df.empty: return "Could not generate heatmap for any of the given tickers."

    # --- Plotting logic is unchanged ---
    fig, ax = plt.subplots(figsize=(10, len(indicator_df) * 0.5))
    ax.axis('off')
    colors = [[(0.8, 0.2, 0.2), (0.2, 0.8, 0.2)][val == 'Yes'] if val in ['Yes', 'No'] else (0.9,0.9,0.9) for val in indicator_df['Above_SMA50']]
    sl_colors = [[(0.8, 0.2, 0.2), (0.2, 0.8, 0.2)][val == 'Up'] if val in ['Up', 'Down'] else (0.9,0.9,0.9) for val in indicator_df['SMA20_Slope']]
    rsi_values = pd.to_numeric(indicator_df['RSI'], errors='coerce')
    rsi_norm = mcolors.Normalize(vmin=20, vmax=80)
    rsi_colors = plt.cm.RdYlGn_r(rsi_norm(rsi_values))
    table_data = indicator_df.values.T
    cell_colours = [rsi_colors.tolist()] + [colors] + [sl_colors]
    table = ax.table(cellText=[[f'{v:.1f}' if isinstance(v, float) else v for v in row] for row in table_data],
                     rowLabels=indicator_df.columns, colLabels=indicator_df.index,
                     cellColours=cell_colours, cellLoc='center', loc='center')
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1.2, 1.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    plt.close(fig)
    return buf

# --- Streamlit User Interface (is unchanged) ---
st.set_page_config(layout="wide")
st.title("📈 Advanced AI Analyst")
st.header("Delta Ghost 📈 Price Chart")
chart_ticker_input = st.text_input("Enter stock tickers separated by commas:", "AAPL, MSFT, NVDA", key="chart_input")
if st.button("Generate Chart"):
    if chart_ticker_input:
        with st.spinner("Generating chart..."):
            result = generate_price_chart(chart_ticker_input)
            if isinstance(result, str): st.error(result)
            else: st.image(result)
    else: st.warning("Please enter at least one ticker for the chart.")
st.markdown("---")
st.header("📊 𝚫👻 Indicators Heatmap")
heatmap_ticker_input = st.text_input("Enter stock tickers for the heatmap:", "TSLA, RIVN, LCID, VRT, FDX, HIMS", key="heatmap_input")
if st.button("Generate Heatmap"):
    if heatmap_ticker_input:
        with st.spinner("Generating heatmap..."):
            result = generate_technical_heatmap(heatmap_ticker_input)
            if isinstance(result, str): st.error(result)
            else: st.image(result)
    else: st.warning("Please enter at least one ticker for the heatmap.")
st.markdown("---")
st.header("👻𝚫 Delta Ghost Research Assistant")
if 'agent_executor' not in st.session_state:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import Tool, AgentExecutor, create_react_agent, hub
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"])
    tools = [Tool(name="Google_Search_for_news", func=Google_Search_for_news, description="Use to search for recent news on a company or topic.")]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    st.session_state.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
ai_question = st.text_input
