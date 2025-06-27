### app.py
import streamlit as st
from agent import run_query

st.set_page_config(page_title="NFL Stat Agent", page_icon="🏈")
st.title("🏈 NFL Stat Agent")

query = st.text_input("Ask a question about NFL stats:")

if query:
    with st.spinner("Thinking..."):
        answer = run_query(query)
        st.markdown("### Answer:")
        st.write(answer)