# Deploy Streamlit UI to Railway

This guide shows how to deploy the Streamlit frontend as a separate service on Railway.

## Prerequisites

- Railway account
- Backend already deployed at: `https://thoughtful-ai-customer-support-agent-production.up.railway.app`

## Deployment Steps

### Option 1: Railway Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Open https://railway.app/dashboard
   - Click on your existing project

2. **Add New Service**
   - Click **"+ New"** button
   - Select **"GitHub Repo"**
   - Choose your `thoughtful-ai-customer-support-agent` repository
   - Railway will create a new service

3. **Configure the Service**
   - Click on the new service
   - Go to **"Settings"** tab
   - Under **"Build"**, set:
     - **Builder**: Dockerfile
     - **Dockerfile Path**: `Dockerfile.streamlit`

4. **Set Environment Variables**
   - Go to **"Variables"** tab
   - Add the following variable:
     ```
     API_BASE_URL=https://thoughtful-ai-customer-support-agent-production.up.railway.app
     ```

5. **Generate Domain**
   - Go to **"Settings"** tab
   - Scroll to **"Networking"** section
   - Click **"Generate Domain"**
   - Railway will create a public URL for your Streamlit UI

6. **Deploy**
   - Railway will automatically deploy
   - Wait for deployment to complete (2-3 minutes)

7. **Access Your UI**
   - Once deployed, click the generated domain
   - You'll see the Streamlit chat interface
   - Share this URL with anyone!

### Option 2: Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Create new service
railway service create streamlit-ui

# Set environment variable
railway variables set API_BASE_URL=https://thoughtful-ai-customer-support-agent-production.up.railway.app

# Deploy
railway up --service streamlit-ui --dockerfile Dockerfile.streamlit

# Generate domain
railway domain
```

## Architecture After Deployment

```
┌─────────────────────────────────────────────────────┐
│                   Railway Project                    │
│                                                      │
│  ┌──────────────────┐      ┌───────────────────┐   │
│  │  Backend Service │      │ Frontend Service  │   │
│  │   (FastAPI)      │◄─────┤  (Streamlit)      │   │
│  │                  │ HTTP │                   │   │
│  │  Port: 8080      │      │  Port: 8501       │   │
│  └──────────────────┘      └───────────────────┘   │
│         │                           │               │
│         │                           │               │
│  backend-xxx.railway.app    streamlit-xxx.railway.app
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Expected URLs

After deployment, you'll have:

- **Backend API**: `https://thoughtful-ai-customer-support-agent-production.up.railway.app`
- **Streamlit UI**: `https://thoughtful-ai-customer-support-agent-production-streamlit.up.railway.app` (or similar)

## Verification

1. **Check Backend Health**:
   ```bash
   curl https://thoughtful-ai-customer-support-agent-production.up.railway.app/health
   ```

2. **Open Streamlit UI**:
   - Open the Streamlit URL in browser
   - Try asking: "What is EVA?"
   - Check debug mode to see agent execution

3. **Test End-to-End**:
   - Ask multiple questions
   - Verify exact matches return instantly
   - Check metrics dashboard

## Troubleshooting

### Streamlit Won't Start

**Issue**: Service crashes on startup

**Solution**: Check Railway logs for errors. Common issues:
- Missing `API_BASE_URL` environment variable
- Wrong Dockerfile path

### Can't Connect to Backend

**Issue**: Streamlit shows connection errors

**Solution**: 
- Verify `API_BASE_URL` is set correctly
- Check backend is running: `curl https://your-backend-url/health`
- Ensure no trailing slash in `API_BASE_URL`

### Port Issues

**Issue**: "Port already in use"

**Solution**: Railway automatically assigns ports. The `${PORT}` variable in Dockerfile handles this.

## Cost Considerations

Railway free tier includes:
- $5 free credit per month
- Enough for 2 small services (backend + frontend)
- Monitor usage in Railway dashboard

For production use, consider:
- Railway Pro plan ($20/month)
- Or deploy Streamlit elsewhere (Streamlit Cloud, Vercel, etc.)

## Alternative: Streamlit Cloud

If you prefer free Streamlit hosting:

1. Go to https://streamlit.io/cloud
2. Connect your GitHub repo
3. Set environment variable: `API_BASE_URL=https://your-backend-url`
4. Deploy

Streamlit Cloud is free for public repos and handles Streamlit apps well.

## Updating the UI

After making changes to `app.py`:

```bash
git add app.py
git commit -m "Update Streamlit UI"
git push origin main
```

Railway will automatically redeploy both services.

## Security Notes

- CORS is disabled in Streamlit for Railway compatibility
- Backend has CORS configured to allow all origins (development mode)
- For production, update CORS settings in `src/main.py`
- Never commit API keys - use Railway environment variables

## Support

If you encounter issues:
1. Check Railway deployment logs
2. Verify environment variables are set
3. Test backend independently
4. Check GitHub repository settings
