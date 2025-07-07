import streamlit as st
from agent import run_query_hybrid, get_debug_logs
from datetime import datetime
from typing import Optional
import time

# Configure page
st.set_page_config(
    page_title="NFL Stat Agent",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stTextInput input {
        font-size: 18px;
    }
    .history-item {
        padding: 8px;
        margin: 4px 0;
        border-radius: 4px;
        cursor: pointer;
    }
    .history-item:hover {
        background-color: #f0f2f6;
    }
    .debug-container {
        font-family: monospace;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_query' not in st.session_state:
    st.session_state.current_query = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Sidebar configuration
with st.sidebar:
    st.title("Settings")
    
    # Dark mode toggle
    st.session_state.dark_mode = st.toggle(
        "Dark Mode",
        value=st.session_state.dark_mode,
        key="dark_mode_toggle"
    )
    
    st.header("Query History")
    
    # Filter history
    search_term = st.text_input("Search history", "")
    
    # Display filtered history
    history_filtered = [
        item for item in st.session_state.query_history
        if search_term.lower() in item[0].lower()
    ]
    
    for i, item in enumerate(reversed(history_filtered)):
        # Handle both old format (4 items) and new format (5 items with reasoning)
        if len(item) == 4:
            q, a, ts, debug = item
            reasoning = None
        else:
            q, a, ts, debug, reasoning = item
            
        with st.container():
            cols = st.columns([1, 4])
            with cols[0]:
                st.text(ts.strftime("%H:%M"))
            with cols[1]:
                if st.button(
                    f"{q[:30]}{'...' if len(q) > 30 else ''}",
                    key=f"hist_{i}",
                    use_container_width=True
                ):
                    st.session_state.current_query = q

# Main content area
st.title("🏈 NFL Stat Agent")
st.markdown("Ask questions about NFL play-by-play and team statistics")

# Query input with clear button
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        "Ask a question about NFL stats:",
        value=st.session_state.current_query or "",
        key="query_input",
        label_visibility="collapsed",
        placeholder="e.g. Which team had the most passing yards in 2022?"
    )
with col2:
    if st.button("Clear", use_container_width=True):
        query = ""
        st.session_state.current_query = None
        st.rerun()

# Example queries
st.markdown("**Example queries:**")
examples = st.columns(3)
with examples[0]:
    if st.button("Top 5 rushers in 2022"):
        query = "Who were the top 5 rushers in 2022?"
with examples[1]:
    if st.button("Best passing team in 2023"):
        query = "Which team had the most passing yards in 2023?"
with examples[2]:
    if st.button("Most common play type"):
        query = "What was the most common play type in the 2023 season?"

# Process query
if query and query != st.session_state.get('last_processed_query', ''):
    st.session_state.last_processed_query = query
    timestamp = datetime.now()
    
    with st.spinner("Analyzing your question..."):
        progress_bar = st.progress(0)
        
        # Simulate progress (in real app, you might update this based on actual progress)
        for percent in range(0, 101, 10):
            time.sleep(0.1)
            progress_bar.progress(percent)
        
        # Time the query
        start_time = time.time()
        result = run_query_hybrid(query, show_reasoning=True)
        elapsed = time.time() - start_time
        answer, error, reasoning = result
        
        # Get debug logs for history and data source
        debug_logs = get_debug_logs()
        if "web_search" in debug_logs.lower():
            source_icon = "🌐 Web Search"
            data_source = "web"
        elif "sql" in debug_logs.lower() or "database" in debug_logs.lower():
            source_icon = "📊 Database"
            data_source = "database"
        else:
            source_icon = "🔄 Hybrid"
            data_source = "hybrid"
        
        # Save to history
        st.session_state.query_history.append(
            (query, answer, timestamp, debug_logs, reasoning)
        )
        
        progress_bar.empty()
        
        # Display results
        if error:
            st.error(f"Error: {error}")
        else:
            # Show reasoning chain if available
            if reasoning:
                st.info(f"🤔 **Thinking:** {reasoning}")
            
            st.markdown(f"**Data Source:** {source_icon} &nbsp;&nbsp; **Response Time:** ⏱️ {elapsed:.2f}s")
            st.markdown("### Answer:")
            st.markdown(f"<div style='background-color:#f8f9fa; padding:15px; border-radius:10px;'>{answer}</div>", 
                        unsafe_allow_html=True)
            
            with st.expander("View Debug Details", expanded=False):
                st.code(debug_logs, language="text")