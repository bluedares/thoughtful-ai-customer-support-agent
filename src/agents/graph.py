"""LangGraph workflow definition for multi-agent orchestration."""

from typing import Literal

from langgraph.graph import StateGraph, END

from src.agents.state import AgentState
from src.agents.router_agent import router_agent
from src.agents.general_agent import general_agent
from src.utils.logger import get_logger

logger = get_logger(__name__)


def route_query(state: AgentState) -> Literal["rag_agent", "general_agent"]:
    """Conditional routing based on router decision.
    
    Args:
        state: Current agent state
        
    Returns:
        Next agent to invoke
    """
    route = state.get("route_decision", "general")
    
    logger.info(
        "routing_decision",
        trace_id=state["metadata"].get("trace_id"),
        route=route,
    )
    
    if route == "rag":
        return "rag_agent"
    else:
        return "general_agent"


def create_agent_graph(rag_agent_instance):
    """Create and compile the agent workflow graph.
    
    Args:
        rag_agent_instance: Initialized RAG agent (needs vector store)
        
    Returns:
        Compiled LangGraph application
    """
    # Create workflow
    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node("router_agent", router_agent)
    workflow.add_node("rag_agent", rag_agent_instance)
    workflow.add_node("general_agent", general_agent)

    # Set entry point
    workflow.set_entry_point("router_agent")

    # Add conditional routing from router
    workflow.add_conditional_edges(
        "router_agent",
        route_query,
        {
            "rag_agent": "rag_agent",
            "general_agent": "general_agent",
        },
    )

    # Both agents end the workflow
    workflow.add_edge("rag_agent", END)
    workflow.add_edge("general_agent", END)

    # Compile the graph
    app = workflow.compile()

    logger.info("agent_graph_compiled", nodes=["router_agent", "rag_agent", "general_agent"])

    return app


def get_graph_structure() -> dict:
    """Get the structure of the agent graph for visualization.
    
    Returns:
        Graph structure as dictionary
    """
    return {
        "nodes": [
            {"id": "router_agent", "type": "classifier", "description": "Routes queries to appropriate agent"},
            {"id": "rag_agent", "type": "retrieval", "description": "Answers using knowledge base"},
            {"id": "general_agent", "type": "conversation", "description": "Handles general queries"},
        ],
        "edges": [
            {"from": "START", "to": "router_agent", "type": "entry"},
            {"from": "router_agent", "to": "rag_agent", "condition": "route == 'rag'"},
            {"from": "router_agent", "to": "general_agent", "condition": "route == 'general'"},
            {"from": "rag_agent", "to": "END", "type": "exit"},
            {"from": "general_agent", "to": "END", "type": "exit"},
        ],
        "routing_logic": (
            "Router agent classifies query as 'rag' (product-related) or 'general' (conversation). "
            "RAG agent retrieves from ChromaDB and answers with context. "
            "General agent provides conversational responses."
        ),
    }
