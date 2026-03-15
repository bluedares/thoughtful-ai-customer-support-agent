# Thoughtful AI Multi-Agent Support System

## Project Overview

A production-ready, scalable AI customer support system built with **LangGraph multi-agent architecture**, **Claude Sonnet 4.5**, and **comprehensive observability**.

### Purpose
Build an intelligent support agent for Thoughtful AI that:
- Answers product questions (EVA, CAM, PHIL) using RAG
- Handles general conversations with Claude
- Provides full transparency into agent execution
- Scales easily with new agents and capabilities

### Key Innovation: Multi-Agent Architecture
Unlike simple RAG systems, this uses **LangGraph** to orchestrate multiple specialized agents:
- **Router Agent**: Classifies queries and routes to appropriate agent
- **RAG Agent**: Retrieves from knowledge base and answers with context
- **General Agent**: Handles non-product conversations
- **Response Formatter**: Standardizes output with metadata

### Observability First
Every agent execution is fully traceable:
- Execution path tracking
- State snapshots at each step
- Performance metrics per agent
- Token usage breakdown
- Debug UI for visualization

## Tech Stack

### Core AI
- **LangGraph 0.0.55**: Multi-agent orchestration with state management
- **LangChain 0.1.20**: Agent tools and utilities
- **Claude Sonnet 4.5** (`claude-sonnet-4-20250514`): Latest Anthropic model
- **ChromaDB 0.4.24**: Vector database for RAG

### Backend
- **FastAPI 0.109.0**: REST API with auto-documentation
- **Pydantic V2**: Type-safe data validation
- **Uvicorn**: ASGI server

### Frontend
- **Streamlit 1.31.0**: Interactive chat UI with debug panel

### Observability
- **structlog 24.1.0**: Structured JSON logging
- **prometheus-client 0.19.0**: Metrics collection
- **OpenTelemetry 1.22.0**: Distributed tracing

### DevOps
- **Docker**: Multi-stage containerization
- **Railway**: Cloud deployment platform

## Project Structure

```
ThoughfulAI/
├── src/
│   ├── agents/              # LangGraph multi-agent system
│   │   ├── graph.py         # StateGraph orchestration
│   │   ├── router_agent.py  # Query classification
│   │   ├── rag_agent.py     # RAG-based answers
│   │   ├── general_agent.py # General conversation
│   │   └── state.py         # Shared agent state
│   │
│   ├── services/
│   │   ├── vector_store.py  # ChromaDB management
│   │   └── llm_client.py    # Claude API wrapper
│   │
│   ├── utils/
│   │   ├── observability.py # Agent tracing & metrics
│   │   ├── debug_middleware.py # Debug tooling
│   │   └── logger.py        # Structured logging
│   │
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings management
│   └── models.py            # Pydantic models
│
├── app.py                   # Streamlit frontend
├── data/qa_dataset.json     # Knowledge base
├── Dockerfile               # Container definition
├── docker-compose.yml       # Local development
└── railway.json             # Deployment config
```

## Agent Flow

```
User Query
    ↓
Router Agent (Claude Sonnet 4.5)
    ├─→ Product-related? → RAG Agent
    │                       ├─→ Retrieve from ChromaDB
    │                       └─→ Answer with context
    │
    └─→ General query? → General Agent
                          └─→ Direct Claude response
    ↓
Response Formatter
    └─→ Add metadata, trace ID, metrics
    ↓
Return to User
```

## Key Features

### 1. Multi-Agent Orchestration
- **LangGraph StateGraph**: Manages agent workflow
- **Conditional Routing**: Dynamic agent selection
- **State Persistence**: Shared context across agents
- **Error Recovery**: Graceful fallbacks

### 2. RAG Pipeline
- **ChromaDB**: Persistent vector storage
- **HuggingFace Embeddings**: `all-MiniLM-L6-v2`
- **Top-K Retrieval**: Get 3 most similar documents
- **Context Injection**: Pass to Claude with query

### 3. Observability & Debugging
- **Agent Tracer**: Track execution flow with trace IDs
- **State Inspector**: Snapshot state at each step
- **Metrics Collector**: Performance and token usage
- **Debug UI**: Visual execution timeline in Streamlit
- **API Endpoints**: `/metrics`, `/traces/{id}`, `/debug/state/{id}`

### 4. Production Ready
- **Docker**: Multi-stage builds for optimization
- **Railway**: One-click cloud deployment
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured JSON logs with correlation IDs
- **Testing**: >80% coverage with pytest

## Development Workflow

### Local Development
```bash
# Backend
uvicorn src.main:app --reload --port 8000

# Frontend
streamlit run app.py
```

### Docker Development
```bash
docker-compose up --build
```

### Deployment
```bash
# Railway auto-deploys from GitHub
# Configure env vars in Railway dashboard
```

## Observability Features

### Agent Execution Tracking
Every request gets a unique trace ID that tracks:
1. Which agents were invoked
2. State transitions between agents
3. Execution time per agent
4. Token usage per agent
5. Success/failure status

### Debug Panel (Streamlit)
- **Agent Flow Diagram**: Visual graph of execution
- **State Inspector**: View state at each step
- **Performance Metrics**: Timing and token breakdown
- **Error Details**: Full stack traces

### Metrics Dashboard
- Total queries processed
- RAG vs General routing split
- Average response times
- Success rates
- Token usage trends

### API Endpoints
- `GET /metrics`: Prometheus-compatible metrics
- `GET /traces/{trace_id}`: Detailed execution trace
- `GET /debug/state/{session_id}`: Current agent state
- `GET /agent-status`: Agent graph structure

## Scalability

### Easy to Extend
Adding new agents is simple:
1. Create new agent file in `src/agents/`
2. Add node to LangGraph workflow
3. Update routing logic
4. Deploy

### Example Extensions
- **Escalation Agent**: Route complex queries to human
- **Feedback Agent**: Collect user satisfaction
- **Analytics Agent**: Generate usage reports
- **Multi-language Agent**: Translate responses

## Performance Targets

- **Response Time**: <3 seconds (RAG), <2 seconds (General)
- **Availability**: 99.9% uptime
- **Token Efficiency**: <1000 tokens per query
- **Vector Search**: <100ms latency

## Security

- API keys in environment variables
- CORS middleware configured
- Input validation with Pydantic
- Rate limiting on endpoints
- No PII in logs

## Monitoring

- Structured logs to stdout (Railway captures)
- Metrics exposed for Prometheus
- Health check endpoint
- Error tracking with context

## Success Criteria

✅ Multi-agent routing works correctly
✅ RAG retrieves relevant documents
✅ Full execution traceability
✅ Debug UI shows agent flow
✅ Metrics dashboard functional
✅ Dockerized and deployed
✅ >80% test coverage
