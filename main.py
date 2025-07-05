import streamlit as st
import os
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(page_title="Delta Ghost AI", layout="wide")

# Title
st.title("📈 Delta Ghost AI: Smart Trade Reports")

# Input box for ticker
ticker = st.text_input("Enter a ticker (e.g., TSLA, AAPL):")

# If no ticker is entered, stop execution
if not ticker:
    st.stop()

# Prompt to generate
prompt = f"""{ticker.upper()} is a publicly traded company. Provide analysis including:
- Stock overview
- Risk
- Opportunity
- Market sentiment
- Google Trends or public sentiment (if available)

Summarize it as if you're preparing a short investment summary for a smart retail trader.
"""

# Load API keys
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

# === Setup OpenAI ===
openai_client = OpenAI(api_key=openai_api_key)

# === Setup Gemini ===
genai.configure(api_key=google_api_key)

# === Layout for dual summaries ===
col1, col2 = st.columns(2)

# === ChatGPT ===
with col1:
    st.subheader("🧠 ChatGPT Summary")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional financial analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        summary = response.choices[0].message.content
        st.success("✅ ChatGPT Responded")
        st.markdown(summary)
    except Exception as e:
        st.error(f"❌ ChatGPT Error:\n\n{str(e)}")

# === Gemini ===
with col2:
    st.subheader("🌐 Gemini Summary")
    try:
        gemini_model = genai.GenerativeModel("gemini-pro")
        gemini_response = gemini_model.generate_content(prompt)
        st.success("✅ Gemini Responded")
        st.markdown(gemini_response.text)
    except Exception as e:
        st.error(f"❌ Gemini Error:\n\n{str(e)}")

# === Raw prompt at bottom ===
with st.expander("📄 Raw Text (Used for Summary)"):
    st.code(prompt)
