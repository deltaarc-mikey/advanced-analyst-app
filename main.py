import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
UW_API_KEY = os.getenv("UW_API_KEY")  # <- Paste your key into .env file as UW_API_KEY

# Streamlit UI
st.set_page_config(page_title="Delta Ghost AI: Options Screener", layout="wide")
st.title("📊 Delta Ghost AI: Options Chain Screener")

ticker = st.text_input("Enter a ticker symbol (e.g., TSLA, AAPL):")

if ticker:
    st.info(f"🔍 Fetching options data for {ticker.upper()}...")

    # API Call
    endpoint = f"https://phx.unusualwhales.com/api/historic_chains/{ticker}"
    headers = {"Authorization": f"Bearer {UW_API_KEY}"}
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        chains = response.json().get("chains", [])

        # Filter: Ask < $0.50 and Volume > 1000
        filtered = [
            c for c in chains
            if c.get("ask", 999) < 0.5 and c.get("volume", 0) > 1000
        ]

        if filtered:
            st.success(f"✅ Found {len(filtered)} qualifying contracts:")
            for contract in filtered:
                st.write({
                    "Symbol": contract.get("ticker"),
                    "Strike": contract.get("strike"),
                    "Type": contract.get("type"),
                    "Expiration": contract.get("expiration"),
                    "Ask": contract.get("ask"),
                    "Volume": contract.get("volume"),
                })
        else:
            st.warning("⚠️ No contracts matched the criteria (ask < $0.50, volume > 1000).")
    else:
        st.error(f"❌ API Error {response.status_code}: {response.text}")
