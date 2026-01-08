import streamlit as st
from openai import OpenAI

def get_client() -> OpenAI:
    """
    Input:
      - OPENAI_API_KEY from Streamlit secrets

    Process:
      - initializes OpenAI client

    Output:
      - OpenAI client instance
    """
    api_key = st.secrets["OPENAI_API_KEY"]
    return OpenAI(api_key=api_key)

def chat(model: str, system: str, user: str) -> str:
    """
    Input:
      - model: model id string
      - system: system instruction text
      - user: user prompt text

    Process:
      - calls OpenAI chat completion

    Output:
      - assistant text
    """
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

