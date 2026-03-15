# Technology Stack & Decisions

## Core Technologies

### 1. LangGraph (v0.0.55)

**Why LangGraph?**
- **Multi-Agent Orchestration**: Built specifically for coordinating multiple AI agents
- **State Management**: Built-in state persistence across agent transitions
- **Conditional Routing**: Easy to define complex agent workflows
- **Observability**: Native support for tracking agent execution
- **Scalability**: Easy to add new agents without refactoring

**Alternatives Considered:**
- ❌ **LangChain Agents**: Less structured, harder to debug
- ❌ **Custom Orchestration**: Reinventing the wheel, more bugs
- ❌ **Simple if/else**: Not scalable, no state management

**Key Features Used:**
- `StateGraph`: Define agent workflow as a graph
- `add_node()`: Register agents
- `add_conditional_edges()`: Dynamic routing
- `compile()`: Create executable graph

### 2. Claude Sonnet 4.5 (claude-sonnet-4-20250514)

**Why Claude Sonnet 4.5?**
- **Latest Model**: Most recent Anthropic release (as of March 2026)
- **Balanced Performance**: Great quality/speed/cost ratio
- **Long Context**: 200k token context window
- **Function Calling**: Good for structured outputs
- **Reliability**: Consistent, predictable responses

**Why Not Claude Opus 4.6?**
- Opus is more expensive
- Sonnet 4.5 is sufficient for this use case
- Faster response times with Sonnet

**Alternatives Considered:**
- ❌ **GPT-4**: Less reliable for structured tasks
- ❌ **Open Source LLMs**: Require self-hosting, less capable
- ❌ **Claude 3.x**: Older, less capable

**Usage:**
- Router Agent: Classification
- RAG Agent: Context-based answering
- General Agent: Conversation

### 3. ChromaDB (v0.4.24)

**Why ChromaDB?**
- **Persistent Storage**: Data survives restarts
- **Easy Setup**: No external database needed
- **Embedding Management**: Automatic embedding generation
- **Fast Similarity Search**: Optimized for retrieval
- **Python Native**: Seamless integration

**Alternatives Considered:**
- ❌ **Pinecone**: Requires external service, costs money
- ❌ **Weaviate**: More complex setup
- ❌ **FAISS**: No persistence out of the box
- ❌ **Qdrant**: Overkill for this scale

**Configuration:**
```python
PersistentClient(path="./chroma_db")
collection.add(
    documents=[...],
    embeddings=HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
)
```

### 4. FastAPI (v0.109.0)

**Why FastAPI?**
- **Performance**: Async support, fast execution
- **Auto Documentation**: Swagger UI out of the box
- **Type Safety**: Pydantic integration
- **Modern**: Python 3.11+ features
- **Easy Testing**: Built-in test client

**Alternatives Considered:**
- ❌ **Flask**: Synchronous, no auto docs
- ❌ **Django**: Too heavy for this use case
- ❌ **Express (Node)**: Different language, less AI library support

**Key Features:**
- Async endpoints for concurrent requests
- Pydantic models for validation
- Middleware for observability
- Auto-generated OpenAPI docs

### 5. Streamlit (v1.31.0)

**Why Streamlit?**
- **Rapid Development**: Build UI in pure Python
- **Interactive**: Built-in session state
- **Chat Components**: Native chat interface
- **Easy Deployment**: Works with Railway
- **Debug Friendly**: Easy to add debug panels

**Alternatives Considered:**
- ❌ **Gradio**: Less customizable
- ❌ **React + FastAPI**: More development time
- ❌ **CLI**: Not user-friendly enough

**Key Features:**
- `st.chat_message()`: Chat bubbles
- `st.session_state`: Persistent state
- `st.expander()`: Collapsible debug info
- `st.tabs()`: Metrics dashboard

### 6. Pydantic V2 (v2.6.0)

**Why Pydantic V2?**
- **Type Safety**: Runtime validation
- **Performance**: 5-50x faster than V1
- **Settings Management**: Environment variable handling
- **JSON Schema**: Auto-generate schemas
- **IDE Support**: Excellent autocomplete

**Usage:**
```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    source: Literal["rag", "general"]
    retrieved_docs: Optional[List[Dict]]
    agent_path: List[str]
    trace_id: str
```

## Observability Stack

### 7. structlog (v24.1.0)

**Why structlog?**
- **Structured Logging**: JSON output for easy parsing
- **Context Binding**: Add trace_id to all logs
- **Performance**: Fast, async-friendly
- **Flexibility**: Custom processors

**Configuration:**
```python
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
```

**Log Format:**
```json
{
  "event": "agent_invoked",
  "agent": "router_agent",
  "trace_id": "abc123",
  "timestamp": "2026-03-15T13:47:00Z",
  "level": "info"
}
```

### 8. Prometheus Client (v0.19.0)

**Why Prometheus?**
- **Industry Standard**: Widely adopted
- **Pull-Based**: Scrape metrics endpoint
- **Time Series**: Track metrics over time
- **Alerting**: Set up alerts on metrics

**Metrics Exposed:**
```python
# Counters
agent_invocations_total{agent="router_agent"} 150
token_usage_total{agent="rag_agent", model="claude-sonnet-4"} 45000

# Histograms
agent_duration_seconds_bucket{agent="rag_agent", le="1.0"} 120
agent_duration_seconds_bucket{agent="rag_agent", le="2.0"} 145

# Gauges
active_sessions 5
vector_store_documents 5
```

### 9. OpenTelemetry (v1.22.0)

**Why OpenTelemetry?**
- **Distributed Tracing**: Track requests across services
- **Vendor Neutral**: Works with any backend
- **Auto-Instrumentation**: Minimal code changes
- **Context Propagation**: Trace IDs across boundaries

**Usage:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("rag_agent") as span:
    span.set_attribute("query", query)
    # Agent logic
    span.set_attribute("docs_retrieved", len(docs))
```

## DevOps Stack

### 10. Docker

**Why Docker?**
- **Consistency**: Same environment everywhere
- **Isolation**: No dependency conflicts
- **Portability**: Run anywhere
- **Railway Compatible**: Native support

**Multi-Stage Build:**
```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11. Railway

**Why Railway?**
- **Easy Deployment**: Git push to deploy
- **Free Tier**: Good for demos
- **Environment Management**: Easy env var setup
- **Monitoring**: Built-in logs and metrics
- **PostgreSQL**: Easy to add if needed

**Alternatives Considered:**
- ❌ **Heroku**: More expensive
- ❌ **AWS**: Too complex for this scale
- ❌ **Vercel**: Not ideal for Python backends
- ❌ **DigitalOcean**: Requires more setup

## Development Tools

### 12. pytest (v8.0.0)

**Why pytest?**
- **Simple**: Easy to write tests
- **Fixtures**: Reusable test setup
- **Parametrization**: Test multiple cases
- **Coverage**: Built-in coverage reports

**Test Structure:**
```python
def test_router_agent_classification():
    state = {"user_query": "What is EVA?"}
    result = router_agent(state)
    assert result["route_decision"] == "rag"

@pytest.mark.parametrize("query,expected", [
    ("What is EVA?", "rag"),
    ("Hello", "general"),
])
def test_router_decisions(query, expected):
    state = {"user_query": query}
    result = router_agent(state)
    assert result["route_decision"] == expected
```

### 13. black (v24.1.1) & ruff (v0.2.0)

**Why black + ruff?**
- **Consistency**: Automatic code formatting
- **Speed**: Ruff is 10-100x faster than pylint
- **Opinionated**: No configuration needed
- **IDE Integration**: Works with VS Code, PyCharm

**Configuration:**
```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
```

## Embedding Model

### 14. all-MiniLM-L6-v2 (HuggingFace)

**Why this model?**
- **Free**: No API costs
- **Fast**: 384-dimensional embeddings
- **Good Quality**: Sufficient for Q&A matching
- **Small**: 80MB model size
- **Offline**: No external API needed

**Alternatives Considered:**
- ❌ **OpenAI text-embedding-3-small**: Costs money
- ❌ **BGE-large**: Slower, larger
- ❌ **E5-base**: Similar performance, less popular

**Performance:**
- Embedding time: ~10ms per query
- Similarity search: <100ms for 5 documents

## Design Decisions

### Why Multi-Agent vs Simple RAG?

**Simple RAG:**
```python
def answer(query):
    docs = retrieve(query)
    return llm(f"Context: {docs}\nQuery: {query}")
```

**Multi-Agent (Our Choice):**
```python
def answer(query):
    route = router_agent(query)  # Classify first
    if route == "rag":
        return rag_agent(query)  # Retrieve + answer
    else:
        return general_agent(query)  # Direct answer
```

**Benefits:**
1. **Better UX**: General queries don't see irrelevant context
2. **Efficiency**: Skip retrieval when not needed
3. **Scalability**: Easy to add more agents (escalation, feedback)
4. **Observability**: Track which path was taken
5. **Accuracy**: Specialized agents for different query types

### Why Observability First?

**Without Observability:**
- User: "Why did I get this answer?"
- Developer: "¯\\_(ツ)_/¯"

**With Observability:**
- User: "Why did I get this answer?"
- Developer: "Let me check trace abc123... Router classified as 'rag', retrieved docs X, Y, Z, Claude generated answer in 1.2s using 300 tokens"

**Benefits:**
1. **Debugging**: Quickly identify issues
2. **Optimization**: Find bottlenecks
3. **Trust**: Show users why they got an answer
4. **Compliance**: Audit trail for decisions
5. **Improvement**: Data-driven enhancements

## Version Pinning Strategy

**Exact Versions:**
- Core dependencies (FastAPI, LangChain, etc.)
- Ensures reproducible builds
- Prevents breaking changes

**Update Strategy:**
- Review changelogs before updating
- Test in staging first
- Update one dependency at a time

## Future Considerations

### Potential Additions:
1. **Redis**: Session management, caching
2. **PostgreSQL**: Persistent chat history
3. **Celery**: Async task processing
4. **Sentry**: Error tracking
5. **Grafana**: Metrics visualization
6. **LangSmith**: LangChain-specific observability

### Scaling Path:
1. **Phase 1** (Current): Single container, ChromaDB
2. **Phase 2**: Separate backend/frontend containers
3. **Phase 3**: External vector DB (Pinecone/Qdrant)
4. **Phase 4**: Kubernetes, auto-scaling
5. **Phase 5**: Multi-region deployment
