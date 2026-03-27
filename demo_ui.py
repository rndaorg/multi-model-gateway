import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="LLM Gateway Demo", layout="wide")

st.title("🌐 Multi-Model API Gateway Demo")
st.markdown("Test routing strategies: **Cost** vs **Performance** vs **Fallback**")

# Sidebar for configuration
st.sidebar.header("Configuration")
strategy = st.sidebar.selectbox("Routing Strategy", ["performance", "cost", "balanced"])
api_url = st.sidebar.text_input("Gateway URL", "http://localhost:8000")

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "strategy": strategy
            }
            response = requests.post(f"{api_url}/v1/chat/completions", json=payload, timeout=30)
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            metadata = data["gateway_metadata"]
            
            message_placeholder.markdown(content)
            
            # Show Metadata Metrics
            st.metrics(
                label="Model Used", 
                value=metadata["model_used"], 
                delta=f"{metadata['latency_s']}s latency"
            )
            st.info(f"💰 Estimated Cost: ${data['usage']['estimated_cost_usd']}")
            
            st.session_state.messages.append({"role": "assistant", "content": content})
            
        except Exception as e:
            st.error(f"Gateway Error: {e}")

# Usage Dashboard
st.divider()
st.subheader("📊 Real-Time Traffic & Cost Log")
try:
    stats = requests.get(f"{api_url}/usage/stats").json()
    if stats['logs']:
        df = pd.DataFrame(stats['logs'])
        st.dataframe(df)
        total_cost = sum(df['cost'])
        st.metric("Total Session Cost", f"${total_cost:.6f}")
    else:
        st.write("No requests logged yet.")
except:
    st.write("Waiting for gateway stats...")
