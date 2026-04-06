import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🚀 Production Multi-Model Gateway")

API_URL = "http://localhost:8000"
API_KEY = "demo-key-123"

# Sidebar: Health Status
st.sidebar.header("System Status")
try:
    health = requests.get(f"{API_URL}/health/models").json()
    for model, status in health.items():
        color = "🟢" if status == "healthy" else "🔴"
        st.sidebar.write(f"{color} {model}: {status}")
except:
    st.sidebar.error("Gateway Offline")

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Stream enabled by default..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # Streaming Request
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "strategy": "cost",
                "stream": True
            }
            headers = {"x-api-key": API_KEY}
            
            with requests.post(f"{API_URL}/v1/chat/completions", json=payload, headers=headers, stream=True) as r:
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith(" "):
                            content = decoded[6:]
                            if content == "[DONE]":
                                break
                            if content.startswith("[ERROR]"):
                                st.error(content)
                                break
                            full_response += content
                            placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Connection Error: {e}")

# DB Stats
st.divider()
st.subheader("💰 Cost & Usage Analytics (From PostgreSQL)")
# Note: In a real app, you'd create an endpoint to fetch DB logs securely
# For demo, we simulate fetching from the /usage/stats endpoint if you kept it, 
# or query DB directly (not recommended for frontend).
st.info("Analytics are being persisted to PostgreSQL. Check DB directly for billing reports.")
