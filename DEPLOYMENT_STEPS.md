# 🚀 LangGraph Cloud Deployment Steps

## Prerequisites
- GitHub account
- LangSmith Plus account (for Cloud deployment)

## Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `langgraph-ghl-booking-python`
3. Description: "Python WhatsApp booking system with GoHighLevel integration"
4. Make it public or private
5. DO NOT initialize with README

## Step 2: Push Code to GitHub
```bash
cd /Users/jaimeortiz/Visual Studio/AI Outlet Media/langgraph-ghl-booking-python

# Remove old remote
git remote remove origin

# Add new remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/langgraph-ghl-booking-python.git

# Create initial commit if needed
git add .
git commit -m "Initial commit: Python GHL booking system"

# Push to GitHub
git push -u origin main
```

## Step 3: Deploy to LangGraph Cloud
1. Go to https://smith.langchain.com/
2. Navigate to LangGraph Platform section
3. Click "New Deployment"
4. Select your GitHub repository
5. Choose deployment settings:
   - Name: `ghl-booking-python`
   - Type: Development (free)
   - Branch: main
   - Auto-deploy: Yes

## Step 4: Configure Environment Variables
In LangGraph Platform deployment settings:
```
OPENAI_API_KEY=sk-...
GHL_API_KEY=your_ghl_api_key
GHL_LOCATION_ID=your_location_id
GHL_WEBHOOK_SECRET=your_webhook_secret
LANGSMITH_API_KEY=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
LANGSMITH_TRACING=true
```

## Step 5: Verify Deployment
1. Wait for deployment to complete (2-3 minutes)
2. Check deployment URL
3. Test health endpoint: `https://your-deployment.us.langgraph.app/health`
4. Update WhatsApp webhook to new URL

## Alternative: Local Testing with LangGraph Studio
```bash
# In project directory
source venv/bin/activate
langgraph dev

# This starts local development server
# Access at http://localhost:8123
# Studio UI at the provided URL
```

## Notes
- The old TypeScript deployment can be deleted once Python is live
- Development deployments are free with unlimited executions
- Production deployments can handle 500 req/sec when needed