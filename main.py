import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import io
import pandas as pd

plt.switch_backend('agg')

def generate_price_chart(tickers_string):
    """
    Generates a comparative stock price chart for a given list of tickers.
    This final version includes a fallback to the 'Close' price.
    """
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
    if not tickers:
        return "No tickers provided."

    raw_data = yf.download(tickers, period='1y', progress=False)

    if raw_data.empty:
        return f"Could not find any data for the tickers: {', '.join(tickers)}."

    # --- FINAL FIX: Fallback from 'Adj Close' to 'Close' ---
    if 'Adj Close' in raw_data.columns:
        price_data = raw_data['Adj Close']
        price_label = 'Adjusted Close Price'
    elif 'Close' in raw_data.columns:
        price_data = raw_data['Close']
        price_label = 'Close Price'
    else:
        return "Could not find 'Adj Close' or 'Close' columns in the downloaded data."
    # --- END OF FIX ---

    if isinstance(price_data, pd.Series):
         price_data = price_data.to_frame(name=tickers[0])

    price_data.dropna(axis=1, how='all', inplace=True)
    if price_data.empty:
         return f"All tickers provided were invalid or had no data: {', '.join(tickers)}."

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

# --- Streamlit User Interface ---
st.set_page_config(layout="wide")
st.title("📈 Advanced AI Analyst")
st.write("This tool allows you to generate visual charts for stock analysis.")

st.header("Comparative Price Chart")
ticker_input = st.text_input("Enter stock tickers separated by commas:", "AAPL, MSFT, NVDA")

if st.button("Generate Chart"):
    if ticker_input:
        with st.spinner("Generating chart..."):
            result = generate_price_chart(ticker_input)
            if isinstance(result, str):
                st.error(result)
            elif result:
                st.image(result, caption=f"Price comparison for {ticker_input.upper()}")
    else:
        st.warning("Please enter at least one ticker symbol.")
