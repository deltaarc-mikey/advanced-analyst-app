import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import io
import pandas as pd

plt.switch_backend('agg')

def generate_price_chart(tickers_string):
    """
    Generates a comparative stock price chart for a given list of tickers.
    This version includes robust error handling for yfinance data.
    """
    tickers = [ticker.strip().upper() for ticker in tickers_string.split(',') if ticker.strip()]
    if not tickers:
        return "No tickers provided."

    # Download historical data
    raw_data = yf.download(tickers, period='1y', progress=False)

    # --- FINAL FIX WITH ERROR HANDLING ---
    # 1. Check if the download returned any data at all.
    if raw_data.empty:
        return f"Could not find any data for the tickers: {', '.join(tickers)}."

    # 2. Select the 'Adj Close' data. This is now the only data we care about.
    if 'Adj Close' in raw_data.columns:
        adj_close_data = raw_data['Adj Close']
    else:
        # If for some reason 'Adj Close' is not a column, we cannot proceed.
        return "The downloaded data is not in the expected format (missing 'Adj Close')."

    # 3. For single tickers, yfinance might not create a top-level 'Adj Close'.
    # We handle this by checking if we have a simple Series or a DataFrame.
    if isinstance(adj_close_data, pd.Series):
         # Convert a single stock's data into a DataFrame for consistent plotting
         adj_close_data = adj_close_data.to_frame(name=tickers[0])

    # 4. Drop columns for any tickers that failed to download (all NaN values)
    adj_close_data.dropna(axis=1, how='all', inplace=True)
    if adj_close_data.empty:
         return f"All tickers provided were invalid or had no data: {', '.join(tickers)}."
    # --- END OF FIX ---

    # Create a plot
    fig, ax = plt.subplots(figsize=(12, 7))
    adj_close_data.plot(ax=ax)

    ax.set_title('Stock Price Comparison (Last Year)', fontsize=16)
    ax.set_ylabel('Adjusted Close Price (USD)', fontsize=12)
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
            # Check if the result is an image buffer or an error string
            if isinstance(result, str):
                st.error(result)
            elif result:
                st.image(result, caption=f"Price comparison for {ticker_input.upper()}")
    else:
        st.warning("Please enter at least one ticker symbol.")
