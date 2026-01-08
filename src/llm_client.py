import streamlit as st
import google.generativeai as genai

def chat(model: str, system: str, user: str) -> str:
    """
    Google Gemini chat wrapper
    """
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)

    full_prompt = f"""
SYSTEM:
{system}

USER:
{user}
"""

    model_obj = genai.GenerativeModel(model)
    response = model_obj.generate_content(
        full_prompt,
        generation_config={
            "temperature": 0.2,
        },
    )

    return response.text.strip()
