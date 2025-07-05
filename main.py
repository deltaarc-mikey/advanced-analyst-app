import streamlit as st
import openai
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# UI Title
st.title("📈 Delta Ghost AI: Smart Trade Reports")
ticker = st.text_input("Enter a ticker (e.g., TSLA, AAPL):")

if ticker:
    raw_prompt = f"""{ticker.upper()} is a publicly traded company. Provide analysis including stock overview, risk, opportunity, and sentiment.
Also include Reddit sentiment if available and any recent spikes in Google Trends. """

    st.markdown("## 🧠 ChatGPT Summary")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional financial analyst."},
                {"role": "user", "content": raw_prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        gpt_summary = response['choices'][0]['message']['content']
        st.success("✅ ChatGPT Responded")
        st.write(gpt_summary)

    except Exception as e:
        st.error(f"❌ ChatGPT Error:\n\n{e}")

    st.markdown("## 🌐 Gemini Summary")
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
        gemini_response = model.generate_content(raw_prompt)
        st.success("✅ Gemini Responded")
        st.write(gemini_response.text)

    except Exception as e:
        st.error(f"❌ Gemini Error:\n\n{e}")

    st.markdown("## 🗂️ Raw Text (Used for Summary)")
    with st.expander("Click to view raw input"):
        st.code(raw_prompt)
