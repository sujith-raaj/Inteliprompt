import os
import uuid
import requests
import streamlit as st

BASE_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))


def get_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def optimize_prompt(prompt: str, target_llm: str) -> dict:
    response = requests.post(f"{BASE_URL}/prompt/optimize", json={
        "original_prompt": prompt,
        "target_llm": target_llm,
        "session_id": get_session_id(),
    })
    response.raise_for_status()
    return response.json()


def get_history() -> list:
    response = requests.get(f"{BASE_URL}/history/", params={"session_id": get_session_id()})
    response.raise_for_status()
    return response.json()


def delete_history_item(item_id: int) -> dict:
    response = requests.delete(f"{BASE_URL}/history/{item_id}")
    response.raise_for_status()
    return response.json()
