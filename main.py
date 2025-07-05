import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import io
import pandas as pd

# Set a non-interactive backend for Matplotlib
plt.switch_backend('agg')

def generate_price_chart(tickers_string):
    """
    Generates a comparative stock price chart for a given list of tickers.
    The input should be a string of tickers separated by commas.
    Returns the chart as an image in an in-memory buffer.
    """
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',')]
    if not tickers:
        return None

    # Download historical data
    raw_data = yf.download(tickers, period='1y')

    # --- THIS IS THE FIX ---
    # Select only the 'Adj Close' data, handling both single and multiple tickers
    if isinstance(raw_data.columns, pd.MultiIndex):
        # For multiple tickers, select the top-level 'Adj Close'
        data_to_plot = raw_data['Adj Close']
    else:
        # For a single ticker, 'Adj Close' is a direct column
        data_to_plot = raw_data[['Adj Close']]
    # --- END OF FIX ---

    # Create a plot
    fig, ax = plt.subplots(figsize=(12, 7))
    data_to_plot.plot(ax=ax)

    # Set chart titles and labels
    ax.set_title('Stock Price Comparison (Last Year)', fontsize=16)
    ax.set_ylabel('Adjusted Close Price (USD)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.grid(True)
    ax.legend(title='Tickers')

    # Save the plot to an in-memory buffer
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
            chart_image = generate_price_chart(ticker_input)
            if chart_image:
                st.image(chart_image, caption=f"Price comparison for {ticker_input.upper()}")
            else:
                st.error("Please enter valid ticker symbols.")
    else:
        st.warning("Please enter at least one ticker symbol.")
