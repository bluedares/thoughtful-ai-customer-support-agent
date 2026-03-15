# Deployment Guide

## Overview

This guide covers deploying the Thoughtful AI Support System to various environments.

## Prerequisites

- Python 3.11+
- Anthropic API key
- Docker (for containerized deployment)
- Git

## Local Development

### 1. Clone Repository

```bash
git clone <repository-url>
cd ThoughfulAI
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

### 5. Run Backend

```bash
uvicorn src.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

### 6. Run Frontend (New Terminal)

```bash
streamlit run app.py
```

Frontend will be available at: http://localhost:8501

### 7. Verify

- Open http://localhost:8501
- Try asking: "What is EVA?"
- Check debug mode for agent execution path

## Docker Deployment

### Local Docker

#### Build Image

```bash
docker build -t thoughtful-ai-support .
```

#### Run Container

```bash
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key-here \
  -v $(pwd)/chroma_db:/app/chroma_db \
  thoughtful-ai-support
```

### Docker Compose

#### Start Services

```bash
docker-compose up --build
```

This starts:
- Backend on http://localhost:8000
- Frontend on http://localhost:8501

#### Stop Services

```bash
docker-compose down
```

#### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Railway Deployment

### Prerequisites

1. Railway account (https://railway.app)
2. GitHub repository
3. Anthropic API key

### Deployment Steps

#### 1. Connect Repository

1. Go to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will detect `railway.json`

#### 2. Configure Environment Variables

In Railway dashboard, add:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### 3. Deploy

Railway will automatically:
- Build the Docker image
- Deploy the container
- Assign a public URL

#### 4. Monitor

- View logs in Railway dashboard
- Check metrics
- Monitor deployment status

#### 5. Custom Domain (Optional)

1. Go to Settings → Domains
2. Add custom domain
3. Configure DNS records

### Railway Configuration

The `railway.json` file configures:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn src.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Deploying Frontend Separately

If you want to deploy Streamlit separately:

1. Create a new Railway service
2. Use the same repository
3. Set start command:
   ```bash
   streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```
4. Set environment variable:
   ```
   API_BASE_URL=https://your-backend-url.railway.app
   ```

## Production Checklist

### Security

- [ ] API keys in environment variables (not in code)
- [ ] `.env` file in `.gitignore`
- [ ] CORS configured for production domains
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Input validation active

### Performance

- [ ] ChromaDB persistence configured
- [ ] Connection pooling enabled
- [ ] Logging level set to INFO or WARN
- [ ] Health checks configured
- [ ] Metrics endpoint secured

### Monitoring

- [ ] Structured logging enabled
- [ ] Prometheus metrics exposed
- [ ] Error tracking configured
- [ ] Health check endpoint tested
- [ ] Alerts configured

### Testing

- [ ] All endpoints tested
- [ ] Agent routing verified
- [ ] RAG retrieval working
- [ ] Pattern matching tested
- [ ] Error handling verified

## Environment Variables

### Required

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Optional (with defaults)

```bash
# Environment
ENVIRONMENT=development  # or production
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR

# Server
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# RAG
TOP_K_RESULTS=3
SIMILARITY_THRESHOLD=0.5
COLLECTION_NAME=thoughtful_ai_qa
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Claude
CLAUDE_MODEL=claude-sonnet-4-20250514
MAX_TOKENS=1000
TEMPERATURE=0.3

# Observability
ENABLE_TRACING=true
ENABLE_METRICS=true
```

## Troubleshooting

### Backend Won't Start

**Issue**: `ModuleNotFoundError`

**Solution**:
```bash
pip install -r requirements.txt
```

**Issue**: `ANTHROPIC_API_KEY not found`

**Solution**:
```bash
# Check .env file exists
cat .env

# Verify API key is set
echo $ANTHROPIC_API_KEY
```

### ChromaDB Errors

**Issue**: `Collection not found`

**Solution**:
```bash
# Delete and reinitialize
rm -rf chroma_db/
# Restart backend - it will recreate
```

**Issue**: `Permission denied`

**Solution**:
```bash
chmod -R 755 chroma_db/
```

### Docker Issues

**Issue**: `Port already in use`

**Solution**:
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
docker run -p 8001:8000 ...
```

**Issue**: `Build failed`

**Solution**:
```bash
# Clean build
docker build --no-cache -t thoughtful-ai-support .
```

### Railway Issues

**Issue**: `Build failed`

**Solution**:
- Check Railway logs
- Verify `railway.json` is correct
- Ensure `Dockerfile` is in root

**Issue**: `Application crashed`

**Solution**:
- Check environment variables
- Verify API key is set
- Check logs for errors

## Monitoring & Logs

### Local Development

**Backend Logs**:
```bash
# Logs appear in terminal running uvicorn
# Structured JSON format in production
```

**Frontend Logs**:
```bash
# Logs appear in terminal running streamlit
```

### Docker

```bash
# View logs
docker logs <container-id>

# Follow logs
docker logs -f <container-id>

# Last 100 lines
docker logs --tail 100 <container-id>
```

### Railway

1. Go to Railway dashboard
2. Select your project
3. Click "Deployments"
4. View logs in real-time

### Metrics

Access metrics at:
- Aggregated: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:8000/metrics/prometheus`

## Scaling

### Horizontal Scaling

The application is stateless and can be scaled horizontally:

1. **Railway**: Adjust replicas in settings
2. **Docker**: Use Docker Swarm or Kubernetes
3. **Load Balancer**: Distribute traffic across instances

### Vertical Scaling

Increase resources:
- CPU: 1-2 cores recommended
- Memory: 1-2 GB minimum
- Storage: 500 MB for ChromaDB

### Database Scaling

For larger datasets:
1. Use external vector DB (Pinecone, Qdrant)
2. Implement caching layer (Redis)
3. Optimize embedding model

## Backup & Recovery

### ChromaDB Backup

```bash
# Backup
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Restore
tar -xzf chroma_backup_20260315.tar.gz
```

### Configuration Backup

```bash
# Backup environment
cp .env .env.backup

# Backup data
cp data/qa_dataset.json data/qa_dataset.backup.json
```

## Updates & Maintenance

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Update Knowledge Base

1. Edit `data/qa_dataset.json`
2. Reload via API:
   ```bash
   curl -X POST http://localhost:8000/reload-kb
   ```
3. Or restart application

### Update Code

```bash
git pull origin main
pip install -r requirements.txt
# Restart services
```

## Health Checks

### Manual Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "vector_store_status": "healthy",
  "vector_store_doc_count": 5,
  "agent_status": "healthy"
}
```

### Automated Monitoring

Configure health check in Railway:
- Endpoint: `/health`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3

## Support

For issues:
1. Check logs first
2. Review troubleshooting section
3. Check GitHub issues
4. Contact support team
