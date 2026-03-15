# Thoughtful AI Multi-Agent Support System

A production-ready AI customer support system built with **LangGraph multi-agent orchestration**, **Claude Sonnet 4.5**, and **comprehensive observability**.

## 🎯 Features

- **Multi-Agent Architecture**: LangGraph orchestrates Router, RAG, and General agents
- **RAG Pipeline**: ChromaDB vector store for product knowledge retrieval
- **Full Observability**: Trace every agent execution with metrics and debugging
- **Modern Stack**: FastAPI backend, Streamlit frontend, Docker containerization
- **Production Ready**: Railway deployment, health checks, error handling

## 🏗️ Architecture

```
User Query → Router Agent → [RAG Agent OR General Agent] → Response Formatter → User
                ↓                    ↓
           Claude Sonnet 4.5    ChromaDB Vector Store
```

### Agent Flow
1. **Router Agent**: Classifies query as product-related or general
2. **RAG Agent**: Retrieves from knowledge base and answers with context
3. **General Agent**: Handles conversational queries directly
4. **Response Formatter**: Adds metadata, trace ID, and metrics

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key
- Docker (optional)

### Local Development

1. **Clone and setup**
```bash
git clone <repository>
cd ThoughfulAI
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Run backend**
```bash
uvicorn src.main:app --reload --port 8000
```

4. **Run frontend** (in another terminal)
```bash
streamlit run app.py
```

5. **Access**
- Frontend: http://localhost:8501
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
```

## 📊 Observability Features

### Debug Panel (Streamlit)
- Agent execution path visualization
- State snapshots at each step
- Performance metrics per agent
- Token usage breakdown
- Retrieved documents display

### API Endpoints
- `POST /chat` - Main chat endpoint
- `GET /health` - Health check
- `GET /metrics` - Aggregated metrics
- `GET /metrics/prometheus` - Prometheus metrics
- `GET /traces/{trace_id}` - Detailed trace
- `GET /agent-status` - Agent graph structure
- `POST /reload-kb` - Reload knowledge base

### Metrics Tracked
- Total requests (RAG vs General)
- Average response time
- Token usage per agent
- Success/failure rates
- Vector search latency

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t thoughtful-ai-support .
```

### Run Container
```bash
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  -v $(pwd)/chroma_db:/app/chroma_db \
  thoughtful-ai-support
```

## ☁️ Railway Deployment

1. **Connect Repository**
   - Link GitHub repository to Railway
   - Railway will detect `railway.json`

2. **Configure Environment**
   - Add `ANTHROPIC_API_KEY` in Railway dashboard
   - Set `ENVIRONMENT=production`

3. **Deploy**
   - Railway auto-deploys on git push
   - Monitor logs in Railway dashboard

4. **Access**
   - Backend: `https://your-app.railway.app`
   - Add Streamlit service separately if needed

## 📁 Project Structure

```
ThoughfulAI/
├── src/
│   ├── agents/              # LangGraph multi-agent system
│   │   ├── graph.py         # StateGraph orchestration
│   │   ├── router_agent.py  # Query classification
│   │   ├── rag_agent.py     # RAG-based answers
│   │   ├── general_agent.py # General conversation
│   │   └── state.py         # Shared agent state
│   ├── services/
│   │   ├── vector_store.py  # ChromaDB management
│   │   └── llm_client.py    # Claude API wrapper
│   ├── utils/
│   │   ├── observability.py # Agent tracing & metrics
│   │   └── logger.py        # Structured logging
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings management
│   └── models.py            # Pydantic models
├── app.py                   # Streamlit frontend
├── data/qa_dataset.json     # Knowledge base
├── Dockerfile               # Container definition
├── docker-compose.yml       # Local development
└── railway.json             # Deployment config
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (defaults shown)
ENVIRONMENT=development
LOG_LEVEL=INFO
CLAUDE_MODEL=claude-sonnet-4-20250514
MAX_TOKENS=1000
TEMPERATURE=0.3
TOP_K_RESULTS=3
```

### Knowledge Base

Edit `data/qa_dataset.json` to add/modify Q&A pairs:

```json
{
  "questions": [
    {
      "question": "What is EVA?",
      "answer": "EVA automates eligibility verification..."
    }
  ]
}
```

Then reload via API or UI:
```bash
curl -X POST http://localhost:8000/reload-kb
```

## 🎨 Streamlit UI Features

### Chat Interface
- Real-time chat with AI agent
- Message history
- Source badges (🤖 RAG / 💬 General)

### Debug Mode
- Toggle in sidebar
- Shows agent execution path
- Displays performance metrics
- View retrieved documents
- Trace ID for backend correlation

### Metrics Dashboard
- Total queries processed
- RAG vs General split
- Average response times
- Success rates
- Recent trace history

## 📈 Scaling

### Add New Agents

1. Create agent file in `src/agents/`
2. Add node to LangGraph in `src/agents/graph.py`
3. Update routing logic
4. Deploy

Example agents to add:
- **Escalation Agent**: Route complex queries to human
- **Feedback Agent**: Collect user satisfaction
- **Analytics Agent**: Generate usage reports

### Extend Knowledge Base

- Add more Q&A pairs to `data/qa_dataset.json`
- Supports unlimited documents
- Auto-generates embeddings
- Reload without restart

## 🔍 Debugging

### View Logs
```bash
# Docker
docker-compose logs -f backend

# Local
# Logs output to stdout with structured JSON
```

### Trace Requests
```bash
# Get trace details
curl http://localhost:8000/traces/{trace_id}

# View in Streamlit debug panel
# Enable "Debug Mode" in sidebar
```

### Check Health
```bash
curl http://localhost:8000/health
```

## 🛠️ Development

### Code Formatting
```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking
```bash
mypy src/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## 📝 API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **LangGraph** - Multi-agent orchestration
- **Anthropic Claude** - Language model
- **ChromaDB** - Vector database
- **FastAPI** - Web framework
- **Streamlit** - UI framework

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check the [documentation](docs/)

---

Built with ❤️ as a practice project demonstrating multi-agent AI systems
