"""Agent state definition for LangGraph."""

from typing import Any, Dict, List, Optional, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Shared state across all agents in the workflow.
    
    This state is passed between agents and updated at each step.
    LangGraph manages state transitions automatically.
    """

    # User input
    user_query: str
    chat_history: List[BaseMessage]
    session_id: Optional[str]

    # Routing
    route_decision: Optional[str]  # "rag" or "general"

    # RAG-specific
    retrieved_docs: List[Any]  # Documents from vector store

    # Output
    final_answer: str

    # Metadata for observability
    metadata: Dict[str, Any]  # Contains trace_id, agent_path, metrics, etc.
