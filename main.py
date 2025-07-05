import streamlit as st
import pandas as pd
import json
import datetime
from docx import Document
from fpdf import FPDF

# Set Streamlit page config
st.set_page_config(page_title="Delta Ghost AI Trade Engine", layout="wide")

# App Title
st.title("Delta Ghost AI Trade Engine")
st.markdown("Built with Gemini + ChatGPT + Unusual Whales Intelligence")

# Tabs
tabs = st.tabs(["📊 Screener & Charts", "📈 AI Trade Signal Center", "📁 Options & Uploads"])

# --- TAB 1: Screener ---
with tabs[0]:
    st.header("Step 1: Screener & Technical Charts")

    tickers = st.text_area("Paste top tickers (e.g., NVDA, AMD, VRT):", height=100)
    if tickers:
        symbols = [x.strip().upper() for x in tickers.split(",") if x.strip()]
        st.success(f"🟢 {len(symbols)} symbols loaded.")
        st.write(symbols)

# --- TAB 2: AI Trade Signal Generator ---
with tabs[1]:
    st.header("Step 2: AI Signal Engine")

    col1, col2 = st.columns(2)
    with col1:
        gemini_text = st.text_area("Paste Gemini signal (from Google Trends or Chat Export):", height=200)
    with col2:
        gpt_output = st.text_area("Paste ChatGPT output (LLM output from prompt):", height=200)

    if st.button("🧠 Generate Trade Plan"):
        if gemini_text or gpt_output:
            st.subheader("📋 AI-Generated Trade Summary")

            summary = f"""### 🔍 Summary:
**Gemini Insights:**  
{gemini_text if gemini_text else 'N/A'}

**ChatGPT Logic:**  
{gpt_output if gpt_output else 'N/A'}

**🛠️ Recommended Actions:**  
- Review tickers for technical confirmation  
- Queue limit or market orders based on trade confidence  
- Cross-verify against Unusual Whales / Barchart setups"""

            st.markdown(summary)

            # Download Word
            doc = Document()
            doc.add_heading("Delta Ghost Trade Summary", 0)
            doc.add_paragraph(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            doc.add_heading("Gemini Output", level=1)
            doc.add_paragraph(gemini_text)
            doc.add_heading("ChatGPT Output", level=1)
            doc.add_paragraph(gpt_output)
            doc.add_heading("Recommended Strategy", level=1)
            doc.add_paragraph("Review tickers for confirmation. Queue trade setups or alerts.")

            word_file = "/mnt/data/DeltaGhost_Trade_Summary.docx"
            doc.save(word_file)
            st.download_button("⬇️ Download Word Report", data=open(word_file, "rb"), file_name="Trade_Summary.docx")

            # Download PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, f"Delta Ghost Trade Summary\n\nDate: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            pdf.multi_cell(0, 10, f"\nGemini Output:\n{gemini_text}")
            pdf.multi_cell(0, 10, f"\nChatGPT Output:\n{gpt_output}")
            pdf.multi_cell(0, 10, "\nRecommended Strategy:\nReview tickers for confirmation. Queue trade setups or alerts.")
            pdf_file = "/mnt/data/DeltaGhost_Trade_Summary.pdf"
            pdf.output(pdf_file)
            st.download_button("⬇️ Download PDF Report", data=open(pdf_file, "rb"), file_name="Trade_Summary.pdf")
        else:
            st.warning("Please paste at least one AI input to generate a trade plan.")

# --- TAB 3: Upload + Webhook ---
with tabs[2]:
    st.header("Step 3: Upload Options Chains + TradingView Alerts")

    uploaded_file = st.file_uploader("📁 Upload options chain CSV or alert JSON", type=["csv", "json"])
    if uploaded_file:
        filename = uploaded_file.name
        st.success(f"Uploaded: {filename}")

        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            st.write(df.head())

        elif filename.endswith(".json"):
            alert_data = json.load(uploaded_file)
            st.json(alert_data)

            if isinstance(alert_data, dict):
                st.subheader("🧠 Auto-Generated Alert Summary")
                ticker = alert_data.get("ticker") or alert_data.get("symbol", "Unknown")
                reason = alert_data.get("reason", "No reason provided.")
                strike = alert_data.get("strike", "N/A")
                expiry = alert_data.get("expiry", "N/A")

                st.markdown(f"""📌 **Trade Alert Received**  
- Ticker: `{ticker}`  
- Reason: *{reason}*  
- Strike: `{strike}`  
- Expiry: `{expiry}`  
- Action: Review chart + confirm order manually in TastyTrade  
""")
            else:
                st.warning("JSON does not match expected alert format.")
