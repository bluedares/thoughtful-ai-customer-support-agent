# Documentation Index

Welcome to the Thoughtful AI Support System documentation!

## 📚 Documentation Structure

### Core Documentation

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
   - Component overview
   - Data flow diagrams
   - Agent orchestration
   - Observability infrastructure
   - Performance characteristics

2. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
   - Local development setup
   - Docker deployment
   - Railway cloud deployment
   - Production checklist
   - Troubleshooting

3. **[API.md](API.md)** - API reference
   - Endpoint documentation
   - Request/response schemas
   - Error handling
   - SDK examples
   - Best practices

4. **[GIT_SETUP.md](GIT_SETUP.md)** - Git and version control
   - Repository setup
   - Branch strategy
   - Commit conventions
   - Security best practices
   - Collaboration workflow

### Quick Links

- **Main README**: `../README.md` - Quick start and overview
- **Project Context**: `../.windsurf/project-context.md` - Detailed project info
- **Tech Stack**: `../.windsurf/tech-stack.md` - Technology decisions

## 🚀 Getting Started

### For Developers

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
2. Follow [DEPLOYMENT.md](DEPLOYMENT.md) for local setup
3. Reference [API.md](API.md) for endpoint details
4. Use [GIT_SETUP.md](GIT_SETUP.md) for version control

### For Users

1. Check main [README.md](../README.md) for quick start
2. See [DEPLOYMENT.md](DEPLOYMENT.md) for running the application
3. Use [API.md](API.md) if integrating with the API

### For DevOps

1. Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options
2. Check [ARCHITECTURE.md](ARCHITECTURE.md) for scaling considerations
3. Monitor using endpoints in [API.md](API.md)

## 📖 Documentation Topics

### Architecture

- [Multi-Agent System](ARCHITECTURE.md#component-details)
- [LangGraph Orchestration](ARCHITECTURE.md#3-orchestration-layer-langgraph)
- [Observability Infrastructure](ARCHITECTURE.md#6-observability-layer)
- [Data Flow](ARCHITECTURE.md#data-flow)

### Deployment

- [Local Development](DEPLOYMENT.md#local-development)
- [Docker Setup](DEPLOYMENT.md#docker-deployment)
- [Railway Deployment](DEPLOYMENT.md#railway-deployment)
- [Environment Variables](DEPLOYMENT.md#environment-variables)

### API

- [Chat Endpoint](API.md#1-chat)
- [Health Check](API.md#2-health-check)
- [Metrics](API.md#5-metrics)
- [Tracing](API.md#7-get-trace)

### Git

- [Initial Setup](GIT_SETUP.md#initial-setup)
- [Security Practices](GIT_SETUP.md#security-best-practices)
- [Workflow](GIT_SETUP.md#common-git-workflows)
- [Collaboration](GIT_SETUP.md#collaboration)

## 🔍 Find What You Need

### I want to...

**Understand the system**
→ Read [ARCHITECTURE.md](ARCHITECTURE.md)

**Run it locally**
→ Follow [DEPLOYMENT.md](DEPLOYMENT.md#local-development)

**Deploy to production**
→ See [DEPLOYMENT.md](DEPLOYMENT.md#railway-deployment)

**Integrate with the API**
→ Check [API.md](API.md)

**Contribute code**
→ Read [GIT_SETUP.md](GIT_SETUP.md)

**Debug an issue**
→ Use [API.md](API.md#7-get-trace) for tracing

**Scale the system**
→ See [ARCHITECTURE.md](ARCHITECTURE.md#performance-characteristics)

**Monitor performance**
→ Check [API.md](API.md#6-prometheus-metrics)

## 🛠️ Key Concepts

### Multi-Agent Architecture

The system uses LangGraph to orchestrate multiple specialized agents:
- **Router Agent**: Classifies queries
- **RAG Agent**: Retrieves and answers from knowledge base
- **General Agent**: Handles conversations

Learn more: [ARCHITECTURE.md](ARCHITECTURE.md#4-agent-layer)

### Observability

Every request is fully traceable with:
- Unique trace IDs
- Agent execution paths
- Performance metrics
- Token usage tracking

Learn more: [ARCHITECTURE.md](ARCHITECTURE.md#6-observability-layer)

### Semantic Matching

Queries are matched using embeddings:
- Similarity threshold: 0.5
- Exact matches return predefined answers
- Low similarity triggers LLM generation

Learn more: [ARCHITECTURE.md](ARCHITECTURE.md#rag-agent)

## 📊 Diagrams

All architecture diagrams are in [ARCHITECTURE.md](ARCHITECTURE.md):
- System overview
- Component details
- Data flow
- Deployment architecture

## 🔐 Security

**Important**: Never commit `.env` files or API keys!

See [GIT_SETUP.md](GIT_SETUP.md#security-best-practices) for:
- .gitignore verification
- Secret management
- Pre-commit hooks
- Removing exposed secrets

## 🤝 Contributing

1. Read [GIT_SETUP.md](GIT_SETUP.md#collaboration)
2. Follow commit conventions
3. Create feature branches
4. Submit pull requests
5. Address review comments

## 📞 Support

For help:
1. Check relevant documentation
2. Review [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)
3. Use trace IDs for debugging
4. Check GitHub issues
5. Contact support team

## 📝 Updates

Documentation is versioned with the code. Always refer to the docs in your current branch/tag.

Last updated: 2026-03-15
