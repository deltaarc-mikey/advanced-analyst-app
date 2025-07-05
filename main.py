import streamlit as st
import openai
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load API keys from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set OpenAI key using new client method
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Set Gemini key
genai.configure(api_key=GEMINI_API_KEY)

# UI
st.title("📈 Delta Ghost AI: Smart Trade Reports")
ticker = st.text_input("Enter a ticker (e.g., TSLA, AAPL):")

if ticker:
    raw_prompt = f"""{ticker.upper()} is a publicly traded company. Provide analysis including stock overview, risk, opportunity, and sentiment.
Also include Reddit sentiment if available and any recent spikes in Google Trends."""

    # ChatGPT Summary
    st.markdown("## 🧠 ChatGPT Summary")
    try:
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional financial analyst."},
                {"role": "user", "content": raw_prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        gpt_summary = chat_response.choices[0].message.content
        st.success("✅ ChatGPT Responded")
        st.write(gpt_summary)

    except Exception as e:
        st.error(f"❌ ChatGPT Error:\n\n{e}")

    # Gemini Summary
    st.markdown("## 🌐 Gemini Summary")
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
        gemini_response = model.generate_content(raw_prompt)
        st.success("✅ Gemini Responded")
        st.write(gemini_response.text)

    except Exception as e:
        st.error(f"❌ Gemini Error:\n\n{e}")

    # Raw Input for Debug
    st.markdown("## 🗂️ Raw Text (Used for Summary)")
    with st.expander("Click to view raw input"):
        st.code(raw_prompt)
