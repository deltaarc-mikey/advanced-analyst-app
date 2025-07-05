import os
import yfinance as yf
import streamlit as st
import openai
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

# Streamlit UI
st.set_page_config(page_title="Delta Ghost AI: Smart Trade Reports", layout="wide")
st.title("📈 Delta Ghost AI: Smart Trade Reports")
ticker_input = st.text_input("Enter a ticker (e.g., TSLA, AAPL):", max_chars=10).upper()

if ticker_input:
    try:
        # Pull stock info from yFinance
        ticker_data = yf.Ticker(ticker_input)
        info = ticker_data.info
        business_summary = info.get("longBusinessSummary", "No summary available.")

        # Combine into one input
        raw_text = f"""{ticker_input} is a publicly traded company. Provide analysis including stock overview, risk, opportunity, and sentiment.

{business_summary}
"""

        # --- ChatGPT Summary (OpenAI) ---
        st.subheader("🧠 ChatGPT Summary")
        try:
            chat_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional financial analyst."},
                    {"role": "user", "content": raw_text}
                ]
            )
            gpt_summary = chat_response["choices"][0]["message"]["content"]
            st.success("ChatGPT Summary:")
            st.markdown(gpt_summary)
        except Exception as e:
            st.error(f"❌ ChatGPT Error:\n{str(e)}")

        # --- Gemini Summary ---
        st.subheader("🪐 Gemini Summary")
        try:
            gemini_model = genai.GenerativeModel("gemini-pro")
            gemini_response = gemini_model.generate_content(raw_text)
            st.success("Gemini Summary:")
            st.markdown(gemini_response.text)
        except Exception as e:
            st.error(f"❌ Gemini Error:\n{str(e)}")

        # --- Raw Text Used ---
        st.markdown("### 📄 Raw Text (Used for Summary)")
        with st.expander("Click to view raw input"):
            st.code(raw_text)

    except Exception as e:
        st.error(f"🚫 Error fetching ticker data: {e}")
else:
    st.info("Please enter a ticker to get started.")
