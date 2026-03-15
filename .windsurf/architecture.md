# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                         │
│                  Streamlit UI (Port 8501)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Chat Interface│  │ Debug Panel  │  │   Metrics    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (Port 8000)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer                                │  │
│  │  /chat  /health  /metrics  /traces  /debug/state    │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │         Observability Middleware                      │  │
│  │  • Request Tracing  • Metrics Collection             │  │
│  │  • State Logging    • Error Tracking                 │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │         LANGGRAPH ORCHESTRATOR                        │  │
│  │                                                        │  │
│  │    ┌──────────┐                                       │  │
│  │    │  START   │                                       │  │
│  │    └────┬─────┘                                       │  │
│  │         │                                             │  │
│  │    ┌────▼─────────┐                                   │  │
│  │    │ ROUTER AGENT │ ← Classify query type            │  │
│  │    └────┬─────────┘                                   │  │
│  │         │                                             │  │
│  │    ┌────┴────┐                                        │  │
│  │    │         │                                        │  │
│  │    ▼         ▼                                        │  │
│  │ ┌─────┐  ┌─────────┐                                 │  │
│  │ │ RAG │  │ GENERAL │                                 │  │
│  │ │AGENT│  │  AGENT  │                                 │  │
│  │ └──┬──┘  └────┬────┘                                 │  │
│  │    │          │                                       │  │
│  │    └────┬─────┘                                       │  │
│  │         │                                             │  │
│  │    ┌────▼──────────┐                                  │  │
│  │    │   FORMATTER   │ ← Add metadata                   │  │
│  │    └────┬──────────┘                                  │  │
│  │         │                                             │  │
│  │    ┌────▼─────┐                                       │  │
│  │    │   END    │                                       │  │
│  │    └──────────┘                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────┬────────────────────────┘
             │                      │
    ┌────────▼────────┐    ┌───────▼──────────┐
    │   CHROMADB      │    │ CLAUDE SONNET 4.5│
    │  Vector Store   │    │   (Anthropic)    │
    │                 │    │                  │
    │ • Embeddings    │    │ • Router LLM     │
    │ • Similarity    │    │ • RAG LLM        │
    │ • Top-K Search  │    │ • General LLM    │
    └─────────────────┘    └──────────────────┘
```

## Component Details

### 1. Streamlit Frontend (app.py)

**Responsibilities:**
- User interface for chat interaction
- Debug panel for execution visualization
- Metrics dashboard for monitoring
- Session state management

**Key Features:**
- Real-time chat interface
- Agent execution path visualization
- State inspector for debugging
- Performance metrics display
- Trace ID correlation

**Communication:**
- HTTP requests to FastAPI backend
- WebSocket for streaming (optional)

### 2. FastAPI Backend (src/main.py)

**Responsibilities:**
- REST API endpoints
- Request validation
- LangGraph orchestration
- Response formatting
- Error handling

**Endpoints:**
- `POST /chat`: Main chat endpoint
- `GET /health`: Health check
- `POST /reload-kb`: Reload knowledge base
- `GET /agent-status`: Agent graph info
- `GET /metrics`: Prometheus metrics
- `GET /traces/{trace_id}`: Execution trace
- `GET /debug/state/{session_id}`: State inspection

**Middleware:**
- CORS handling
- Request tracing
- Metrics collection
- Error logging

### 3. LangGraph Orchestrator (src/agents/graph.py)

**Architecture:**
```python
StateGraph(AgentState)
  ├─ router_agent      # Entry point
  ├─ rag_agent         # RAG path
  ├─ general_agent     # General path
  └─ response_formatter # Exit point
```

**State Flow:**
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
        "token_usage": Dict[str, int]
    }
}
```

**Execution Flow:**
1. **Router Agent** receives query
   - Calls Claude to classify query type
   - Updates state with route_decision
   - Logs classification reasoning

2. **Conditional Edge** routes based on decision
   - If "rag" → RAG Agent
   - If "general" → General Agent

3. **RAG Agent** (if routed here)
   - Retrieves top-k docs from ChromaDB
   - Constructs context prompt
   - Calls Claude with context
   - Updates state with answer and docs

4. **General Agent** (if routed here)
   - Calls Claude directly
   - No retrieval needed
   - Updates state with answer

5. **Response Formatter**
   - Adds metadata (trace_id, agent_path, metrics)
   - Formats final response
   - Returns to API layer

### 4. Router Agent (src/agents/router_agent.py)

**Purpose:** Classify queries to route to appropriate agent

**Logic:**
```python
def router_agent(state: AgentState) -> AgentState:
    query = state["user_query"]
    
    # Classify with Claude
    classification_prompt = f"""
    Classify if this query is about Thoughtful AI products 
    (EVA, CAM, PHIL) or general conversation.
    
    Query: {query}
    
    Respond with ONLY: "rag" or "general"
    """
    
    decision = claude.invoke(classification_prompt)
    state["route_decision"] = decision.strip().lower()
    state["metadata"]["agent_path"].append("router")
    
    return state
```

**Observability:**
- Log classification decision
- Track execution time
- Record token usage

### 5. RAG Agent (src/agents/rag_agent.py)

**Purpose:** Answer product questions using retrieved context

**Logic:**
```python
def rag_agent(state: AgentState) -> AgentState:
    query = state["user_query"]
    
    # Retrieve from ChromaDB
    docs = vector_store.similarity_search(query, k=3)
    state["retrieved_docs"] = docs
    
    # Construct prompt with context
    context = "\n\n".join([doc.page_content for doc in docs])
    prompt = f"""
    Context: {context}
    
    Question: {query}
    
    Answer based on the context provided.
    """
    
    answer = claude.invoke(prompt)
    state["final_answer"] = answer
    state["metadata"]["agent_path"].append("rag_agent")
    state["metadata"]["source"] = "rag"
    
    return state
```

**Observability:**
- Log retrieved documents
- Track vector search latency
- Record Claude token usage
- Measure total execution time

### 6. General Agent (src/agents/general_agent.py)

**Purpose:** Handle general conversation

**Logic:**
```python
def general_agent(state: AgentState) -> AgentState:
    query = state["user_query"]
    
    prompt = f"""
    You are a helpful assistant for Thoughtful AI.
    
    User: {query}
    
    Provide a helpful, friendly response.
    """
    
    answer = claude.invoke(prompt)
    state["final_answer"] = answer
    state["metadata"]["agent_path"].append("general_agent")
    state["metadata"]["source"] = "general"
    
    return state
```

**Observability:**
- Log query and response
- Track token usage
- Measure execution time

### 7. Vector Store Service (src/services/vector_store.py)

**Responsibilities:**
- Initialize ChromaDB
- Load Q&A dataset
- Generate embeddings
- Similarity search
- Reload functionality

**Architecture:**
```python
class VectorStoreService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="thoughtful_ai_qa",
            embedding_function=HuggingFaceEmbeddings()
        )
    
    def initialize(self, qa_data: List[Dict]):
        # Convert to LangChain Documents
        docs = [
            Document(
                page_content=f"Q: {qa['question']}\nA: {qa['answer']}",
                metadata={"source": "qa_dataset", "question": qa['question']}
            )
            for qa in qa_data
        ]
        
        # Add to collection
        self.collection.add_documents(docs)
    
    def similarity_search(self, query: str, k: int = 3):
        return self.collection.similarity_search(query, k=k)
```

### 8. Observability System (src/utils/observability.py)

**Components:**

**Agent Tracer:**
```python
class AgentTracer:
    def __init__(self):
        self.traces = {}
    
    def start_trace(self, trace_id: str):
        self.traces[trace_id] = {
            "start_time": time.time(),
            "agents": [],
            "states": []
        }
    
    def log_agent_entry(self, trace_id: str, agent_name: str, state: dict):
        self.traces[trace_id]["agents"].append({
            "name": agent_name,
            "entry_time": time.time(),
            "input_state": state.copy()
        })
    
    def log_agent_exit(self, trace_id: str, agent_name: str, state: dict):
        agent = self.traces[trace_id]["agents"][-1]
        agent["exit_time"] = time.time()
        agent["duration"] = agent["exit_time"] - agent["entry_time"]
        agent["output_state"] = state.copy()
```

**Metrics Collector:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
agent_invocations = Counter('agent_invocations_total', 'Agent invocations', ['agent_name'])
agent_duration = Histogram('agent_duration_seconds', 'Agent execution time', ['agent_name'])
token_usage = Counter('token_usage_total', 'Token usage', ['agent_name', 'model'])
routing_decisions = Counter('routing_decisions_total', 'Routing decisions', ['route'])
```

**State Inspector:**
```python
class StateInspector:
    def snapshot(self, state: AgentState, agent_name: str):
        return {
            "agent": agent_name,
            "timestamp": time.time(),
            "state": state.copy(),
            "diff": self.compute_diff(state)
        }
    
    def compute_diff(self, current_state: dict):
        # Compare with previous state
        # Return changed fields
        pass
```

## Data Flow

### Request Flow
```
1. User sends message via Streamlit
   ↓
2. POST /chat with {"message": "What is EVA?"}
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
8. RAG agent calls Claude with context
   ↓
9. Response formatter adds metadata
   ↓
10. FastAPI returns response with trace_id
   ↓
11. Streamlit displays answer + debug info
```

### State Transitions
```
Initial State:
{
  "user_query": "What is EVA?",
  "chat_history": [],
  "route_decision": null,
  "retrieved_docs": [],
  "final_answer": null,
  "metadata": {"trace_id": "abc123", "agent_path": []}
}

After Router:
{
  ...
  "route_decision": "rag",
  "metadata": {"agent_path": ["router"], ...}
}

After RAG Agent:
{
  ...
  "retrieved_docs": [doc1, doc2, doc3],
  "final_answer": "EVA automates eligibility verification...",
  "metadata": {"agent_path": ["router", "rag_agent"], ...}
}

After Formatter:
{
  ...
  "metadata": {
    "trace_id": "abc123",
    "agent_path": ["router", "rag_agent", "formatter"],
    "source": "rag",
    "execution_times": {"router": 0.5, "rag_agent": 1.2},
    "token_usage": {"router": 50, "rag_agent": 300}
  }
}
```

## Deployment Architecture

### Docker Containers
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

## Scalability Considerations

### Horizontal Scaling
- Stateless API design
- Shared ChromaDB volume
- Session management via external store (future)

### Performance Optimization
- ChromaDB indexing for fast retrieval
- Claude API connection pooling
- Response caching (future)
- Async processing where possible

### Monitoring
- Prometheus metrics export
- Structured logging to stdout
- Trace correlation across services
- Health checks for dependencies
