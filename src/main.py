"""FastAPI application with multi-agent support system."""

import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from src.config import settings
from src.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    AgentStatusResponse,
    MetricsResponse,
    TraceDetail,
    ExecutionMetrics,
    RetrievedDocument,
)
from src.agents.state import AgentState
from src.agents.graph import create_agent_graph, get_graph_structure
from src.agents.rag_agent import RAGAgent
from src.services.vector_store import vector_store_service
from src.utils.logger import setup_logging, get_logger, bind_context, unbind_context
from src.utils.observability import tracer, metrics_collector, state_inspector

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global agent graph (initialized on startup)
agent_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("application_starting", environment=settings.environment)
    
    try:
        # Initialize vector store
        logger.info("initializing_vector_store")
        vector_store_service.initialize()
        
        # Create RAG agent with vector store
        rag_agent = RAGAgent(vector_store_service)
        
        # Create agent graph
        global agent_graph
        agent_graph = create_agent_graph(rag_agent)
        
        logger.info("application_started_successfully")
        
    except Exception as e:
        logger.error("startup_error", error=str(e), exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI app
app = FastAPI(
    title="Thoughtful AI Support System",
    description="Multi-agent AI support system with LangGraph orchestration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint that invokes the agent workflow.
    
    Args:
        request: Chat request with user message
        
    Returns:
        Chat response with answer and metadata
    """
    start_time = time.time()
    
    # Start trace
    trace_id = tracer.start_trace()
    bind_context(trace_id=trace_id, session_id=request.session_id)
    
    logger.info(
        "chat_request_received",
        message=request.message[:100],
        session_id=request.session_id,
    )
    
    try:
        # Initialize agent state
        initial_state: AgentState = {
            "user_query": request.message,
            "chat_history": [],
            "session_id": request.session_id,
            "route_decision": None,
            "retrieved_docs": [],
            "final_answer": "",
            "metadata": {
                "trace_id": trace_id,
                "agent_path": [],
                "source": "",
            },
        }
        
        # Invoke agent graph
        logger.info("invoking_agent_graph", trace_id=trace_id)
        final_state = agent_graph.invoke(initial_state)
        
        # End trace
        trace_data = tracer.end_trace(trace_id)
        
        # Calculate metrics
        total_duration = time.time() - start_time
        agent_durations = trace_data["metrics"]["agent_durations"]
        token_usage = trace_data["metrics"]["token_usage"]
        
        # Record metrics
        metrics_collector.record_request(
            source=final_state["metadata"]["source"],
            duration=total_duration,
            tokens=sum(token_usage.values()),
            success=True,
        )
        
        # Build response
        retrieved_docs = None
        if final_state["retrieved_docs"]:
            retrieved_docs = [
                RetrievedDocument(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=None,
                )
                for doc in final_state["retrieved_docs"]
            ]
        
        response = ChatResponse(
            answer=final_state["final_answer"],
            source=final_state["metadata"]["source"],
            retrieved_docs=retrieved_docs,
            agent_path=final_state["metadata"]["agent_path"],
            trace_id=trace_id,
            model_used=settings.claude_model,
            metrics=ExecutionMetrics(
                total_duration=total_duration,
                agent_durations=agent_durations,
                token_usage=token_usage,
                vector_search_duration=final_state["metadata"].get("vector_search_duration"),
            ),
        )
        
        logger.info(
            "chat_request_completed",
            trace_id=trace_id,
            source=response.source,
            duration_seconds=round(total_duration, 3),
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "chat_request_error",
            trace_id=trace_id,
            error=str(e),
            exc_info=True,
        )
        
        # Record failed request
        metrics_collector.record_request(
            source="error",
            duration=time.time() - start_time,
            tokens=0,
            success=False,
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}",
        )
    
    finally:
        unbind_context("trace_id", "session_id")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint.
    
    Returns:
        Health status of the system
    """
    try:
        # Check vector store
        doc_count = vector_store_service.get_document_count()
        vector_store_status = "healthy" if doc_count > 0 else "empty"
        
        # Check agent graph
        agent_status = "healthy" if agent_graph is not None else "not_initialized"
        
        overall_status = "healthy" if (
            vector_store_status == "healthy" and agent_status == "healthy"
        ) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            vector_store_status=vector_store_status,
            vector_store_doc_count=doc_count,
            agent_status=agent_status,
        )
        
    except Exception as e:
        logger.error("health_check_error", error=str(e), exc_info=True)
        return HealthResponse(
            status="unhealthy",
            vector_store_status="error",
            vector_store_doc_count=0,
            agent_status="error",
        )


@app.post("/reload-kb")
async def reload_knowledge_base() -> dict:
    """Reload the knowledge base from the Q&A dataset.
    
    Returns:
        Status message
    """
    try:
        logger.info("reloading_knowledge_base")
        vector_store_service.reload()
        doc_count = vector_store_service.get_document_count()
        
        logger.info("knowledge_base_reloaded", doc_count=doc_count)
        
        return {
            "status": "success",
            "message": f"Knowledge base reloaded with {doc_count} documents",
            "document_count": doc_count,
        }
        
    except Exception as e:
        logger.error("reload_kb_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error reloading knowledge base: {str(e)}",
        )


@app.get("/agent-status", response_model=AgentStatusResponse)
async def agent_status() -> AgentStatusResponse:
    """Get agent graph structure and status.
    
    Returns:
        Agent status information
    """
    try:
        graph_structure = get_graph_structure()
        
        return AgentStatusResponse(
            available_agents=["router_agent", "rag_agent", "general_agent"],
            graph_structure=graph_structure,
            routing_logic=graph_structure["routing_logic"],
        )
        
    except Exception as e:
        logger.error("agent_status_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting agent status: {str(e)}",
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get aggregated metrics.
    
    Returns:
        System metrics
    """
    try:
        metrics = metrics_collector.get_metrics()
        
        return MetricsResponse(
            total_requests=metrics["total_requests"],
            rag_requests=metrics["rag_requests"],
            general_requests=metrics["general_requests"],
            average_response_time=metrics["average_response_time"],
            success_rate=metrics["success_rate"],
            total_tokens_used=metrics["total_tokens_used"],
        )
        
    except Exception as e:
        logger.error("get_metrics_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting metrics: {str(e)}",
        )


@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint.
    
    Returns:
        Prometheus-formatted metrics
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/traces/{trace_id}", response_model=TraceDetail)
async def get_trace(trace_id: str) -> TraceDetail:
    """Get detailed trace information.
    
    Args:
        trace_id: Trace identifier
        
    Returns:
        Detailed trace information
    """
    try:
        trace_data = tracer.get_trace(trace_id)
        
        if not trace_data:
            raise HTTPException(
                status_code=404,
                detail=f"Trace {trace_id} not found",
            )
        
        # Get state snapshots
        snapshots = state_inspector.get_snapshots(trace_id)
        
        return TraceDetail(
            trace_id=trace_id,
            timestamp=trace_data["timestamp"],
            user_query=trace_data["user_query"],
            agent_path=[agent["name"] for agent in trace_data["agents"]],
            state_snapshots=snapshots,
            metrics=ExecutionMetrics(
                total_duration=trace_data["metrics"]["total_duration"],
                agent_durations=trace_data["metrics"]["agent_durations"],
                token_usage=trace_data["metrics"]["token_usage"],
            ),
            final_answer=trace_data["final_answer"],
            source=trace_data["source"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_trace_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting trace: {str(e)}",
        )


@app.get("/debug/state/{session_id}")
async def get_session_state(session_id: str) -> dict:
    """Get current state for a session (for debugging).
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session state information
    """
    # This would require session state persistence
    # For now, return a placeholder
    return {
        "session_id": session_id,
        "message": "Session state tracking not yet implemented",
        "note": "Use trace_id from chat responses to debug specific requests",
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information.
    
    Returns:
        API information
    """
    return {
        "name": "Thoughtful AI Support System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /chat",
            "health": "GET /health",
            "reload_kb": "POST /reload-kb",
            "agent_status": "GET /agent-status",
            "metrics": "GET /metrics",
            "prometheus": "GET /metrics/prometheus",
            "traces": "GET /traces/{trace_id}",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
