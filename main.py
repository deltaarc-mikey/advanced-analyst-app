import streamlit as st
import requests
import openai
import os
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# App UI
st.set_page_config(page_title="Delta Ghost AI", layout="wide", page_icon="📈")
st.title("📈 Delta Ghost AI: Smart Trade Reports")
ticker = st.text_input("Enter a ticker (e.g., TSLA, AAPL):")

# ChatGPT summary
def summarize_with_chatgpt(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst providing stock summaries with risk, opportunity, and trade recommendations."},
                {"role": "user", "content": f"Summarize this:\n\n{text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ ChatGPT Error: {e}"

# Gemini summary
def summarize_with_gemini(text):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gemini_api_key}"
        }
        payload = {
            "contents": [
                {"parts": [{"text": f"Summarize this financial data and give opportunity, risk, and trade idea:\n\n{text}"}]}
            ]
        }
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"❌ Gemini Error: {e}"

# Data placeholder
sample_text = f"{ticker} is a publicly traded company. Provide analysis including stock overview, risk, opportunity, and sentiment."

if ticker:
    with st.spinner("Analyzing..."):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🧠 ChatGPT Summary")
            chatgpt_summary = summarize_with_chatgpt(sample_text)
            st.write(chatgpt_summary)

        with col2:
            st.subheader("🔮 Gemini Summary")
            gemini_summary = summarize_with_gemini(sample_text)
            st.write(gemini_summary)

    st.divider()
    st.subheader("📉 Raw Text (Used for Summary)")
    st.code(sample_text)
