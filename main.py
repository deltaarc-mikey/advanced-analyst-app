import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import OpenAI (new version syntax)
from openai import OpenAI

# Import Gemini
import google.generativeai as genai

# Configure APIs
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel(model_name="gemini-pro:latest")

# Streamlit UI
st.set_page_config(page_title="Delta Ghost AI", layout="wide")
st.title("📈 Delta Ghost AI: Smart Trade Reports")

ticker = st.text_input("Enter a ticker (e.g., TSLA, AAPL):", max_chars=10)

if ticker:
    prompt = f"""
    {ticker.upper()} is a publicly traded company. Provide analysis including:
    - Stock Overview
    - Risk Factors
    - Opportunity
    - Market Sentiment
    - Google Trends or public buzz
    """

    col1, col2 = st.columns(2)

    # === ChatGPT ===
    with col1:
        st.subheader("🧠 ChatGPT Summary")
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            chatgpt_output = response.choices[0].message.content
            st.success("✅ ChatGPT Responded")
            st.markdown(chatgpt_output)
        except Exception as e:
            st.error(f"❌ ChatGPT Error:\n\n{str(e)}")

    # === Gemini ===
    with col2:
        st.subheader("🌐 Gemini Summary")
        try:
            gemini_response = gemini_model.generate_content(prompt)
            st.success("✅ Gemini Responded")
            st.markdown(gemini_response.text)
        except Exception as e:
            st.error(f"❌ Gemini Error:\n\n{str(e)}")

    # === Show Raw Input ===
    with st.expander("🗂️ Raw Text (Used for Summary)"):
        st.code(prompt)
