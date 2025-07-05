import streamlit as st
import openai
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set page config
st.set_page_config(page_title="📈 Delta Ghost AI: Smart Trade Reports")
st.title("📈 Delta Ghost AI: Smart Trade Reports")

# Ticker Input
ticker = st.text_input("Enter a ticker (e.g., TSLA, AAPL):", max_chars=10)

# Prompt template
prompt_template = """
{ticker} is a publicly traded company. Provide analysis including stock overview, risk, opportunity, and sentiment.
"""

# Output containers
chatgpt_col, gemini_col = st.columns(2)

if ticker:
    prompt = prompt_template.format(ticker=ticker.upper())

    # ChatGPT Summary
    with chatgpt_col:
        st.subheader("🧠 ChatGPT Summary")
        try:
            chatgpt_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional stock analyst."},
                    {"role": "user", "content": prompt}
                ]
            )
            st.success("✅ ChatGPT Responded")
            st.markdown(chatgpt_response.choices[0].message.content)
        except Exception as e:
            st.error(f"❌ ChatGPT Error:\n\n{str(e)}")

    # Gemini Summary
    with gemini_col:
        st.subheader("🌐 Gemini Summary")
        try:
            gemini_model = genai.GenerativeModel("models/gemini-1.5-pro")  # ✅ Fixed model name
            gemini_response = gemini_model.generate_content(prompt)
            st.success("✅ Gemini Responded")
            st.markdown(gemini_response.text)
        except Exception as e:
            st.error(f"❌ Gemini Error:\n\n{str(e)}")

    # Show raw text
    st.markdown("""
    ### 🗂 Raw Text (Used for Summary) ▸
    """)
    with st.expander("Click to view raw input"):
        st.code(prompt)
