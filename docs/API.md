# API Documentation

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-app.railway.app`

## Authentication

Currently, the API does not require authentication. For production, consider adding API key authentication.

## Endpoints

### 1. Chat

Send a message to the AI agent.

**Endpoint**: `POST /chat`

**Request Body**:
```json
{
  "message": "What is EVA?",
  "session_id": "optional-session-id"
}
```

**Request Schema**:
- `message` (string, required): User message (1-2000 characters)
- `session_id` (string, optional): Session identifier for tracking

**Response**:
```json
{
  "answer": "EVA automates the process of verifying a patient's eligibility...",
  "source": "rag",
  "retrieved_docs": [
    {
      "content": "Question: What does EVA do?\nAnswer: EVA automates...",
      "metadata": {
        "source": "qa_dataset",
        "question": "What does the eligibility verification agent (EVA) do?",
        "answer": "EVA automates..."
      },
      "score": null
    }
  ],
  "agent_path": ["router_agent", "rag_agent"],
  "trace_id": "abc123-def456-ghi789",
  "model_used": "claude-sonnet-4-20250514",
  "metrics": {
    "total_duration": 1.234,
    "agent_durations": {
      "router_agent": 0.456,
      "rag_agent": 0.778
    },
    "token_usage": {
      "router_agent": 50,
      "rag_agent": 0
    },
    "vector_search_duration": 0.089
  }
}
```

**Response Fields**:
- `answer` (string): The agent's response
- `source` (string): Response source - "rag" or "general"
- `retrieved_docs` (array, optional): Documents retrieved from vector store
- `agent_path` (array): List of agents invoked
- `trace_id` (string): Unique trace identifier for debugging
- `model_used` (string): LLM model identifier
- `metrics` (object): Execution metrics

**Example**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is EVA?"}'
```

**Status Codes**:
- `200 OK`: Success
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

---

### 2. Health Check

Check system health status.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "vector_store_status": "healthy",
  "vector_store_doc_count": 5,
  "agent_status": "healthy"
}
```

**Response Fields**:
- `status` (string): Overall status - "healthy" or "unhealthy"
- `vector_store_status` (string): Vector store status
- `vector_store_doc_count` (integer): Number of documents loaded
- `agent_status` (string): Agent system status

**Example**:
```bash
curl http://localhost:8000/health
```

**Status Codes**:
- `200 OK`: Always returns 200, check response body for actual status

---

### 3. Reload Knowledge Base

Reload the knowledge base from the Q&A dataset.

**Endpoint**: `POST /reload-kb`

**Response**:
```json
{
  "status": "success",
  "message": "Knowledge base reloaded with 5 documents",
  "document_count": 5
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/reload-kb
```

**Status Codes**:
- `200 OK`: Success
- `500 Internal Server Error`: Reload failed

**Use Case**: Call this after updating `data/qa_dataset.json`

---

### 4. Agent Status

Get agent graph structure and routing information.

**Endpoint**: `GET /agent-status`

**Response**:
```json
{
  "available_agents": [
    "router_agent",
    "rag_agent",
    "general_agent"
  ],
  "graph_structure": {
    "nodes": [
      {
        "id": "router_agent",
        "type": "classifier",
        "description": "Routes queries to appropriate agent"
      },
      {
        "id": "rag_agent",
        "type": "retrieval",
        "description": "Answers using knowledge base"
      },
      {
        "id": "general_agent",
        "type": "conversation",
        "description": "Handles general queries"
      }
    ],
    "edges": [
      {
        "from": "START",
        "to": "router_agent",
        "type": "entry"
      },
      {
        "from": "router_agent",
        "to": "rag_agent",
        "condition": "route == 'rag'"
      },
      {
        "from": "router_agent",
        "to": "general_agent",
        "condition": "route == 'general'"
      }
    ],
    "routing_logic": "Router agent classifies query as 'rag' or 'general'..."
  },
  "routing_logic": "Router agent classifies query as 'rag' (product-related) or 'general' (conversation)..."
}
```

**Example**:
```bash
curl http://localhost:8000/agent-status
```

---

### 5. Metrics

Get aggregated system metrics.

**Endpoint**: `GET /metrics`

**Response**:
```json
{
  "total_requests": 42,
  "rag_requests": 28,
  "general_requests": 14,
  "average_response_time": 1.234,
  "success_rate": 0.976,
  "total_tokens_used": 12500
}
```

**Response Fields**:
- `total_requests` (integer): Total requests processed
- `rag_requests` (integer): Requests routed to RAG agent
- `general_requests` (integer): Requests routed to General agent
- `average_response_time` (float): Average response time in seconds
- `success_rate` (float): Success rate (0-1)
- `total_tokens_used` (integer): Total tokens consumed

**Example**:
```bash
curl http://localhost:8000/metrics
```

---

### 6. Prometheus Metrics

Get metrics in Prometheus format for monitoring.

**Endpoint**: `GET /metrics/prometheus`

**Response**: Prometheus text format
```
# HELP agent_invocations_total Total number of agent invocations
# TYPE agent_invocations_total counter
agent_invocations_total{agent_name="router_agent"} 42.0
agent_invocations_total{agent_name="rag_agent"} 28.0
agent_invocations_total{agent_name="general_agent"} 14.0

# HELP agent_duration_seconds Agent execution duration in seconds
# TYPE agent_duration_seconds histogram
agent_duration_seconds_bucket{agent_name="rag_agent",le="0.1"} 5.0
agent_duration_seconds_bucket{agent_name="rag_agent",le="0.5"} 20.0
...
```

**Example**:
```bash
curl http://localhost:8000/metrics/prometheus
```

**Use Case**: Configure Prometheus to scrape this endpoint

---

### 7. Get Trace

Get detailed execution trace for debugging.

**Endpoint**: `GET /traces/{trace_id}`

**Path Parameters**:
- `trace_id` (string): Trace identifier from chat response

**Response**:
```json
{
  "trace_id": "abc123-def456-ghi789",
  "timestamp": "2026-03-15T14:30:00Z",
  "user_query": "What is EVA?",
  "agent_path": ["router_agent", "rag_agent"],
  "state_snapshots": [
    {
      "agent": "router_agent",
      "stage": "entry",
      "timestamp": 1710512400.123,
      "state": {
        "user_query": "What is EVA?",
        "route_decision": null
      }
    },
    {
      "agent": "router_agent",
      "stage": "exit",
      "timestamp": 1710512400.456,
      "state": {
        "user_query": "What is EVA?",
        "route_decision": "rag"
      }
    }
  ],
  "metrics": {
    "total_duration": 1.234,
    "agent_durations": {
      "router_agent": 0.456,
      "rag_agent": 0.778
    },
    "token_usage": {
      "router_agent": 50,
      "rag_agent": 0
    }
  },
  "final_answer": "EVA automates...",
  "source": "rag"
}
```

**Example**:
```bash
curl http://localhost:8000/traces/abc123-def456-ghi789
```

**Status Codes**:
- `200 OK`: Trace found
- `404 Not Found`: Trace not found

---

### 8. Debug State

Get current state for a session (placeholder for future implementation).

**Endpoint**: `GET /debug/state/{session_id}`

**Response**:
```json
{
  "session_id": "session-123",
  "message": "Session state tracking not yet implemented",
  "note": "Use trace_id from chat responses to debug specific requests"
}
```

**Example**:
```bash
curl http://localhost:8000/debug/state/session-123
```

---

### 9. Root

Get API information.

**Endpoint**: `GET /`

**Response**:
```json
{
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
    "traces": "GET /traces/{trace_id}"
  }
}
```

**Example**:
```bash
curl http://localhost:8000/
```

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to:
- View all endpoints
- See request/response schemas
- Test endpoints directly
- Download OpenAPI spec

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

**Validation Error (422)**:
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Server Error (500)**:
```json
{
  "detail": "Error processing request: Connection timeout"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. For production:

1. Add rate limiting middleware
2. Configure limits per endpoint
3. Return `429 Too Many Requests` when exceeded

## CORS

CORS is configured to allow all origins in development. For production:

```python
# Update in src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Webhooks

Not currently implemented. Future consideration for:
- Async processing notifications
- Long-running task updates
- Event streaming

## Versioning

Current version: `v1` (implicit)

Future versions will use URL versioning:
- `v1`: `/v1/chat`
- `v2`: `/v2/chat`

## SDK Examples

### Python

```python
import httpx

# Chat
response = httpx.post(
    "http://localhost:8000/chat",
    json={"message": "What is EVA?"}
)
data = response.json()
print(data["answer"])

# Health check
health = httpx.get("http://localhost:8000/health").json()
print(f"Status: {health['status']}")
```

### JavaScript

```javascript
// Chat
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'What is EVA?'})
});
const data = await response.json();
console.log(data.answer);

// Health check
const health = await fetch('http://localhost:8000/health').then(r => r.json());
console.log(`Status: ${health.status}`);
```

### cURL

```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is EVA?"}'

# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

## Best Practices

1. **Always check health** before making requests
2. **Use trace_id** for debugging failed requests
3. **Monitor metrics** to track system performance
4. **Handle errors** gracefully in your client
5. **Set timeouts** (30s recommended for chat)
6. **Validate input** before sending to API
7. **Log trace_id** for support requests

## Support

For API issues:
1. Check `/health` endpoint
2. Review trace using `/traces/{trace_id}`
3. Check server logs
4. Contact support with trace_id
