"""Streamlit frontend for Thoughtful AI Support System."""

import json
import time
from datetime import datetime
from typing import Optional

import httpx
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Thoughtful AI Support",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

if "trace_history" not in st.session_state:
    st.session_state.trace_history = []


def call_chat_api(message: str) -> Optional[dict]:
    """Call the chat API endpoint.
    
    Args:
        message: User message
        
    Returns:
        API response or None if error
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{API_BASE_URL}/chat",
                json={"message": message},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        st.error(f"API Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def get_health_status() -> Optional[dict]:
    """Get system health status.
    
    Returns:
        Health status or None if error
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{API_BASE_URL}/health")
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def get_metrics() -> Optional[dict]:
    """Get system metrics.
    
    Returns:
        Metrics or None if error
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{API_BASE_URL}/metrics")
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def reload_knowledge_base() -> bool:
    """Reload the knowledge base.
    
    Returns:
        True if successful
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{API_BASE_URL}/reload-kb")
            response.raise_for_status()
            return True
    except Exception as e:
        st.error(f"Reload error: {str(e)}")
        return False


def render_sidebar():
    """Render the sidebar with controls and status."""
    with st.sidebar:
        st.title("🤖 Thoughtful AI")
        st.markdown("---")
        
        # System Status
        st.subheader("System Status")
        health = get_health_status()
        
        if health:
            status_color = "🟢" if health["status"] == "healthy" else "🔴"
            st.markdown(f"{status_color} **Status:** {health['status'].title()}")
            st.markdown(f"📚 **Documents:** {health['vector_store_doc_count']}")
            st.markdown(f"🤖 **Agents:** {health['agent_status']}")
        else:
            st.markdown("🔴 **Status:** Unable to connect")
        
        st.markdown("---")
        
        # Controls
        st.subheader("Controls")
        
        # Debug mode toggle
        debug_mode = st.checkbox(
            "🔍 Debug Mode",
            value=st.session_state.debug_mode,
            help="Show execution details and agent paths",
        )
        st.session_state.debug_mode = debug_mode
        
        # Reload KB button
        if st.button("🔄 Reload Knowledge Base", use_container_width=True):
            with st.spinner("Reloading..."):
                if reload_knowledge_base():
                    st.success("Knowledge base reloaded!")
                    time.sleep(1)
                    st.rerun()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.trace_history = []
            st.rerun()
        
        st.markdown("---")
        
        # Quick Stats
        if health and health["status"] == "healthy":
            st.subheader("Quick Stats")
            metrics = get_metrics()
            
            if metrics:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Queries", metrics["total_requests"])
                    st.metric("RAG Queries", metrics["rag_requests"])
                with col2:
                    st.metric(
                        "Avg Time",
                        f"{metrics['average_response_time']:.2f}s"
                    )
                    st.metric(
                        "Success Rate",
                        f"{metrics['success_rate']*100:.1f}%"
                    )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        Multi-agent AI support system powered by:
        - **LangGraph** orchestration
        - **Claude Sonnet 4.5**
        - **ChromaDB** vector store
        - **FastAPI** backend
        """)


def render_agent_path(agent_path: list, source: str):
    """Render agent execution path visualization.
    
    Args:
        agent_path: List of agent names
        source: Response source (rag/general)
    """
    st.markdown("**🔀 Agent Execution Path:**")
    
    # Create visual flow
    path_str = " → ".join(agent_path)
    
    # Color code based on source
    if source == "rag":
        st.markdown(f"🤖 `{path_str}` (RAG Pipeline)")
    else:
        st.markdown(f"💬 `{path_str}` (General Conversation)")


def render_metrics_panel(metrics: dict):
    """Render execution metrics panel.
    
    Args:
        metrics: Metrics dictionary
    """
    with st.expander("📊 Execution Metrics", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Total Duration",
                f"{metrics['total_duration']:.3f}s"
            )
            
            # Agent durations
            st.markdown("**Agent Durations:**")
            for agent, duration in metrics['agent_durations'].items():
                st.markdown(f"- `{agent}`: {duration:.3f}s")
        
        with col2:
            # Token usage
            total_tokens = sum(metrics['token_usage'].values())
            st.metric("Total Tokens", total_tokens)
            
            st.markdown("**Token Breakdown:**")
            for agent, tokens in metrics['token_usage'].items():
                st.markdown(f"- `{agent}`: {tokens}")
            
            # Vector search duration
            if metrics.get('vector_search_duration'):
                st.metric(
                    "Vector Search",
                    f"{metrics['vector_search_duration']:.3f}s"
                )


def render_retrieved_docs(docs: list):
    """Render retrieved documents.
    
    Args:
        docs: List of retrieved documents
    """
    with st.expander(f"📚 Retrieved Documents ({len(docs)})", expanded=False):
        for i, doc in enumerate(docs, 1):
            st.markdown(f"**Document {i}:**")
            st.markdown(f"```\n{doc['content']}\n```")
            
            if doc.get('metadata'):
                st.json(doc['metadata'])
            
            if i < len(docs):
                st.markdown("---")


def render_debug_panel(response_data: dict):
    """Render comprehensive debug panel.
    
    Args:
        response_data: Full API response
    """
    st.markdown("---")
    st.markdown("### 🔍 Debug Information")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Agent path
        render_agent_path(
            response_data['agent_path'],
            response_data['source']
        )
        
        # Metrics
        render_metrics_panel(response_data['metrics'])
    
    with col2:
        # Trace info
        st.markdown("**🔖 Trace Info:**")
        st.code(response_data['trace_id'], language=None)
        
        st.markdown("**🤖 Model:**")
        st.code(response_data['model_used'], language=None)
        
        st.markdown("**📍 Source:**")
        badge_color = "🤖" if response_data['source'] == "rag" else "💬"
        st.markdown(f"{badge_color} `{response_data['source'].upper()}`")
    
    # Retrieved documents (if RAG)
    if response_data.get('retrieved_docs'):
        render_retrieved_docs(response_data['retrieved_docs'])


def render_message(role: str, content: str, response_data: Optional[dict] = None):
    """Render a chat message.
    
    Args:
        role: Message role (user/assistant)
        content: Message content
        response_data: Optional response data for assistant messages
    """
    with st.chat_message(role):
        st.markdown(content)
        
        # Show debug info for assistant messages if debug mode is on
        if role == "assistant" and response_data and st.session_state.debug_mode:
            render_debug_panel(response_data)


def render_metrics_dashboard():
    """Render metrics dashboard in a separate tab."""
    st.title("📊 Metrics Dashboard")
    
    metrics = get_metrics()
    
    if not metrics:
        st.error("Unable to fetch metrics")
        return
    
    # Overview stats
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", metrics['total_requests'])
    with col2:
        st.metric("RAG Requests", metrics['rag_requests'])
    with col3:
        st.metric("General Requests", metrics['general_requests'])
    with col4:
        st.metric(
            "Success Rate",
            f"{metrics['success_rate']*100:.1f}%"
        )
    
    # Performance metrics
    st.subheader("Performance")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Average Response Time",
            f"{metrics['average_response_time']:.3f}s"
        )
    with col2:
        st.metric("Total Tokens Used", f"{metrics['total_tokens_used']:,}")
    
    # Routing distribution
    st.subheader("Routing Distribution")
    if metrics['total_requests'] > 0:
        rag_pct = (metrics['rag_requests'] / metrics['total_requests']) * 100
        general_pct = (metrics['general_requests'] / metrics['total_requests']) * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.progress(rag_pct / 100, text=f"RAG: {rag_pct:.1f}%")
        with col2:
            st.progress(general_pct / 100, text=f"General: {general_pct:.1f}%")
    
    # Recent traces
    st.subheader("Recent Traces")
    if st.session_state.trace_history:
        for trace in reversed(st.session_state.trace_history[-10:]):
            with st.expander(
                f"🔖 {trace['trace_id'][:8]}... - {trace['source'].upper()} - {trace['timestamp']}"
            ):
                st.json(trace)
    else:
        st.info("No traces yet. Start chatting to see trace history!")


def main():
    """Main application entry point."""
    # Render sidebar
    render_sidebar()
    
    # Create tabs
    tab1, tab2 = st.tabs(["💬 Chat", "📊 Metrics"])
    
    with tab1:
        # Main chat interface
        st.title("Thoughtful AI Support Agent")
        st.markdown("Ask me about EVA, CAM, PHIL, or anything else!")
        
        # Display chat history
        for message in st.session_state.messages:
            render_message(
                message["role"],
                message["content"],
                message.get("response_data"),
            )
        
        # Chat input
        if prompt := st.chat_input("Ask a question..."):
            # Add user message to session state
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
            })
            
            # Get response from API
            with st.spinner("Thinking..."):
                response_data = call_chat_api(prompt)
            
            if response_data:
                # Add assistant message to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_data["answer"],
                    "response_data": response_data,
                })
                
                # Add to trace history
                st.session_state.trace_history.append({
                    "trace_id": response_data["trace_id"],
                    "timestamp": datetime.now().isoformat(),
                    "source": response_data["source"],
                    "agent_path": response_data["agent_path"],
                    "duration": response_data["metrics"]["total_duration"],
                })
            
            # Rerun to display all messages properly
            st.rerun()
    
    with tab2:
        render_metrics_dashboard()


if __name__ == "__main__":
    main()
