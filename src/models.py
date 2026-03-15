"""Pydantic models for request/response validation."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class RetrievedDocument(BaseModel):
    """Model for retrieved documents from vector store."""

    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    score: Optional[float] = Field(None, description="Similarity score")


class ExecutionMetrics(BaseModel):
    """Execution metrics for observability."""

    total_duration: float = Field(..., description="Total execution time in seconds")
    agent_durations: Dict[str, float] = Field(
        default_factory=dict, description="Duration per agent"
    )
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage per agent")
    vector_search_duration: Optional[float] = Field(
        None, description="Vector search duration in seconds"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    answer: str = Field(..., description="Agent's response")
    source: Literal["rag", "general"] = Field(..., description="Response source type")
    retrieved_docs: Optional[List[RetrievedDocument]] = Field(
        None, description="Retrieved documents (if RAG)"
    )
    agent_path: List[str] = Field(..., description="Agent execution path")
    trace_id: str = Field(..., description="Trace ID for debugging")
    model_used: str = Field(..., description="LLM model used")
    metrics: ExecutionMetrics = Field(..., description="Execution metrics")


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "unhealthy"] = Field(..., description="Health status")
    vector_store_status: str = Field(..., description="Vector store status")
    vector_store_doc_count: int = Field(..., description="Number of documents in vector store")
    agent_status: str = Field(..., description="Agent system status")


class AgentStatusResponse(BaseModel):
    """Agent status response."""

    available_agents: List[str] = Field(..., description="List of available agents")
    graph_structure: Dict[str, Any] = Field(..., description="Agent graph structure")
    routing_logic: str = Field(..., description="Description of routing logic")


class MetricsResponse(BaseModel):
    """Metrics response."""

    total_requests: int = Field(..., description="Total requests processed")
    rag_requests: int = Field(..., description="RAG agent requests")
    general_requests: int = Field(..., description="General agent requests")
    average_response_time: float = Field(..., description="Average response time in seconds")
    success_rate: float = Field(..., description="Success rate (0-1)")
    total_tokens_used: int = Field(..., description="Total tokens used")


class TraceDetail(BaseModel):
    """Detailed trace information."""

    trace_id: str = Field(..., description="Trace identifier")
    timestamp: str = Field(..., description="Trace timestamp")
    user_query: str = Field(..., description="User query")
    agent_path: List[str] = Field(..., description="Agent execution path")
    state_snapshots: List[Dict[str, Any]] = Field(
        ..., description="State snapshots at each step"
    )
    metrics: ExecutionMetrics = Field(..., description="Execution metrics")
    final_answer: str = Field(..., description="Final answer")
    source: str = Field(..., description="Response source")
