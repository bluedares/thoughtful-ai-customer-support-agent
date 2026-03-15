# System Architecture

## Overview

Thoughtful AI Support System is a production-ready multi-agent AI application built with LangGraph orchestration, Claude Sonnet 4.5, and comprehensive observability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (Browser)                          │
│                    Streamlit UI (Port 8501)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Chat         │  │ Debug Panel  │  │ Metrics      │         │
│  │ Interface    │  │ - Agent Path │  │ Dashboard    │         │
│  │              │  │ - Metrics    │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (Port 8000)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                          │  │
│  │  POST /chat  GET /health  GET /metrics  GET /traces      │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │            Observability Middleware                       │  │
│  │  • Request Tracing (trace_id)                            │  │
│  │  • Metrics Collection (Prometheus)                       │  │
│  │  • State Logging (structlog)                             │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │              LANGGRAPH ORCHESTRATOR                       │  │
│  │                                                            │  │
│  │    ┌──────────┐                                           │  │
│  │    │  START   │                                           │  │
│  │    └────┬─────┘                                           │  │
│  │         │                                                 │  │
│  │    ┌────▼─────────┐                                       │  │
│  │    │ ROUTER AGENT │ ← Classify: product vs general       │  │
│  │    │ (Claude API) │                                       │  │
│  │    └────┬─────────┘                                       │  │
│  │         │                                                 │  │
│  │    ┌────┴────┐                                            │  │
│  │    │         │                                            │  │
│  │    ▼         ▼                                            │  │
│  │ ┌─────────┐  ┌──────────────┐                            │  │
│  │ │   RAG   │  │   GENERAL    │                            │  │
│  │ │  AGENT  │  │    AGENT     │                            │  │
│  │ │         │  │              │                            │  │
│  │ │ Pattern │  │ Pattern Check│                            │  │
│  │ │ Check   │  │ (greetings)  │                            │  │
│  │ │   ↓     │  │     ↓        │                            │  │
│  │ │ Exact?  │  │ Match? → Yes │                            │  │
│  │ │ Yes→Ans │  │     ↓        │                            │  │
│  │ │ No→LLM  │  │ No→Claude    │                            │  │
│  │ └──┬──────┘  └──────┬───────┘                            │  │
│  │    │                │                                     │  │
│  │    └────┬───────────┘                                     │  │
│  │         │                                                 │  │
│  │    ┌────▼──────────┐                                      │  │
│  │    │   FORMATTER   │ ← Add metadata, trace_id            │  │
│  │    └────┬──────────┘                                      │  │
│  │         │                                                 │  │
│  │    ┌────▼─────┐                                           │  │
│  │    │   END    │                                           │  │
│  │    └──────────┘                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────┬────────────────────────────┘
             │                      │
    ┌────────▼────────┐    ┌───────▼──────────┐
    │   CHROMADB      │    │ CLAUDE SONNET 4.5│
    │  Vector Store   │    │   (Anthropic)    │
    │                 │    │                  │
    │ • Embeddings    │    │ • Router         │
    │ • Similarity    │    │ • RAG (optional) │
    │ • Top-K Search  │    │ • General        │
    └─────────────────┘    └──────────────────┘
```

## Component Details

### 1. Frontend Layer (Streamlit)

**File**: `app.py`

**Responsibilities**:
- User interface for chat interaction
- Debug panel with execution visualization
- Metrics dashboard
- Session state management

**Key Features**:
- Real-time chat with message history
- Agent execution path visualization
- Performance metrics display
- Trace ID correlation with backend logs

**Technology**: Streamlit 1.31.0

### 2. API Layer (FastAPI)

**File**: `src/main.py`

**Responsibilities**:
- REST API endpoints
- Request validation with Pydantic
- LangGraph orchestration
- Response formatting
- Error handling

**Endpoints**:
```python
POST   /chat              # Main chat endpoint
GET    /health            # Health check
POST   /reload-kb         # Reload knowledge base
GET    /agent-status      # Agent graph structure
GET    /metrics           # Aggregated metrics
GET    /metrics/prometheus # Prometheus format
GET    /traces/{trace_id} # Detailed trace
GET    /debug/state/{id}  # State inspection
```

**Technology**: FastAPI 0.109.0, Uvicorn 0.27.0

### 3. Orchestration Layer (LangGraph)

**File**: `src/agents/graph.py`

**Architecture**:
```python
StateGraph(AgentState)
  ├─ router_agent      # Entry point
  ├─ rag_agent         # RAG path
  ├─ general_agent     # General path
  └─ response_formatter # Exit point
```

**State Management**:
```python
AgentState = {
    "user_query": str,
    "chat_history": List[Message],
    "route_decision": str,  # "rag" or "general"
    "retrieved_docs": List[Document],
    "final_answer": str,
    "metadata": {
        "trace_id": str,
        "agent_path": List[str],
        "execution_times": Dict[str, float],
        "token_usage": Dict[str, int],
        "best_similarity": float,
        "match_type": str  # "exact_match", "llm_generated", "pattern_match"
    }
}
```

**Technology**: LangGraph 0.0.55, LangChain 0.2.0

### 4. Agent Layer

#### Router Agent
**File**: `src/agents/router_agent.py`

**Purpose**: Classify queries as product-related or general conversation

**Logic**:
```python
def router_agent(state):
    # Calls Claude to classify query
    classification = claude.classify(query)
    # Returns "rag" or "general"
    return state with route_decision
```

**Token Usage**: ~50 tokens per classification

#### RAG Agent
**File**: `src/agents/rag_agent.py`

**Purpose**: Answer product questions using knowledge base

**Logic**:
```python
def rag_agent(state):
    # 1. Retrieve from ChromaDB with similarity scores
    docs, scores = vector_store.similarity_search_with_score(query, k=3)
    
    # 2. Calculate similarity (0-1)
    similarity = 1 - (distance / 2)
    
    # 3. Decision based on threshold (0.5)
    if similarity >= 0.5:
        # Return exact answer from dataset
        return extract_exact_answer(best_doc)
    else:
        # Generate answer with Claude using context
        return claude.generate(query, context=docs)
```

**Optimization**: 
- Exact matches: 0 tokens (no LLM call)
- Low similarity: ~800 tokens (LLM generation)

#### General Agent
**File**: `src/agents/general_agent.py`

**Purpose**: Handle general conversation

**Logic**:
```python
def general_agent(state):
    # 1. Check simple patterns first
    if pattern_match(query):
        return pattern_response  # No LLM call
    
    # 2. Generate with Claude
    return claude.generate(query)
```

**Patterns Handled**:
- Greetings: "hi", "hello", "hey"
- Thanks: "thank you", "thanks"
- Personal info: "what is my name"
- Goodbyes: "bye", "goodbye"

**Token Usage**: 
- Pattern match: 0 tokens
- LLM generation: ~500 tokens

### 5. Data Layer

#### Vector Store Service
**File**: `src/services/vector_store.py`

**Technology**: ChromaDB 0.4.24

**Responsibilities**:
- Initialize ChromaDB with persistent storage
- Load Q&A dataset from JSON
- Generate embeddings (all-MiniLM-L6-v2)
- Similarity search with scores
- Reload functionality

**Storage**:
- Path: `./chroma_db/`
- Collection: `thoughtful_ai_qa`
- Documents: 5 Q&A pairs
- Embedding dimension: 384

#### LLM Client
**File**: `src/services/llm_client.py`

**Technology**: Anthropic Claude API

**Features**:
- Retry logic (3 attempts)
- Exponential backoff
- Error handling
- Token counting

### 6. Observability Layer

**Files**: 
- `src/utils/observability.py`
- `src/utils/logger.py`

**Components**:

#### Agent Tracer
```python
class AgentTracer:
    def start_trace(trace_id) -> str
    def log_agent_entry(trace_id, agent_name, state)
    def log_agent_exit(trace_id, agent_name, state, tokens)
    def end_trace(trace_id) -> dict
    def get_trace(trace_id) -> dict
```

#### Metrics Collector
```python
# Prometheus metrics
agent_invocations_total{agent_name}
agent_duration_seconds{agent_name}
token_usage_total{agent_name, model}
routing_decisions_total{route}
vector_search_duration_seconds
```

#### State Inspector
```python
class StateInspector:
    def snapshot(trace_id, agent_name, state, stage)
    def get_snapshots(trace_id) -> List[dict]
    def compute_diff(trace_id, agent_name) -> dict
```

#### Structured Logging
- Format: JSON
- Library: structlog 24.1.0
- Correlation: trace_id in all logs
- Levels: DEBUG, INFO, WARN, ERROR

## Data Flow

### Request Flow

```
1. User sends message via Streamlit
   ↓
2. POST /chat {"message": "What is EVA?"}
   ↓
3. FastAPI creates trace_id, initializes state
   ↓
4. LangGraph invokes router_agent
   ↓
5. Router classifies → "rag"
   ↓
6. LangGraph routes to rag_agent
   ↓
7. RAG agent retrieves docs from ChromaDB
   ↓
8. Similarity check: 0.95 ≥ 0.5 → exact match
   ↓
9. Return exact answer (no Claude call)
   ↓
10. Response formatter adds metadata
   ↓
11. FastAPI returns response with trace_id
   ↓
12. Streamlit displays answer + debug info
```

### State Transitions

```
Initial State:
{
  "user_query": "What is EVA?",
  "route_decision": null,
  "final_answer": null,
  "metadata": {"trace_id": "abc123", "agent_path": []}
}

After Router:
{
  "route_decision": "rag",
  "metadata": {"agent_path": ["router_agent"]}
}

After RAG Agent:
{
  "retrieved_docs": [doc1, doc2, doc3],
  "final_answer": "EVA automates...",
  "metadata": {
    "agent_path": ["router_agent", "rag_agent"],
    "match_type": "exact_match",
    "best_similarity": 0.95
  }
}
```

## Deployment Architecture

### Docker Container
```
┌─────────────────────────────────────┐
│   Docker Container (Railway)        │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   FastAPI    │  │  Streamlit  │ │
│  │  (Port 8000) │  │ (Port 8501) │ │
│  └──────┬───────┘  └──────┬──────┘ │
│         │                 │         │
│  ┌──────▼─────────────────▼──────┐ │
│  │      ChromaDB (Persistent)    │ │
│  │      /app/chroma_db           │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
         │
         ▼
    Railway Platform
    • Auto-scaling
    • Load balancing
    • Monitoring
```

## Performance Characteristics

### Response Times
- Pattern match: <50ms
- Exact match (RAG): <200ms
- LLM generation: 1-3 seconds
- Vector search: <100ms

### Token Usage
- Router: 50 tokens
- RAG (exact): 0 tokens
- RAG (LLM): 800 tokens
- General (pattern): 0 tokens
- General (LLM): 500 tokens

### Scalability
- Stateless API design
- Horizontal scaling ready
- Persistent vector store
- Connection pooling

## Security

### API Keys
- Stored in environment variables
- Never committed to git
- Separate keys per environment

### Input Validation
- Pydantic models for all requests
- Max message length: 2000 chars
- Type checking on all fields

### CORS
- Configurable origins
- Credentials support
- Method restrictions

## Monitoring

### Metrics
- Prometheus endpoint: `/metrics/prometheus`
- Custom metrics for agents
- Token usage tracking
- Success/failure rates

### Logging
- Structured JSON logs
- Trace ID correlation
- Log levels per environment
- Stdout for Railway capture

### Health Checks
- Endpoint: `/health`
- Vector store status
- Agent system status
- Document count

## Future Enhancements

### Planned Features
1. **Escalation Agent**: Route complex queries to human
2. **Feedback Agent**: Collect user satisfaction
3. **Analytics Agent**: Generate usage reports
4. **Multi-language Support**: Translate responses
5. **Session Persistence**: Redis for chat history
6. **Caching**: Response caching for common queries
7. **A/B Testing**: Experiment with different prompts

### Scaling Path
1. **Phase 1** (Current): Single container
2. **Phase 2**: Separate backend/frontend
3. **Phase 3**: External vector DB (Pinecone)
4. **Phase 4**: Kubernetes deployment
5. **Phase 5**: Multi-region setup
