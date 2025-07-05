import streamlit as st
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

client = OpenAI(api_key=openai_key)

def summarize_openai(text):
    try:
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": f"Summarize this: {text}"}
            ]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ ChatGPT Error: {e}"

def summarize_gemini(text):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gemini_key}"
        }
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        payload = {
            "contents": [
                {"parts": [{"text": f"Summarize this: {text}"}]}
            ]
        }
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"❌ Gemini Error: {e}"
