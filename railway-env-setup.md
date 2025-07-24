# Railway Environment Variables Setup

## Project Details
- **Project URL**: https://railway.com/project/666c7460-92e6-4d0a-878b-27edca1b6af4
- **Service**: ghl-langgraph-bridge

## Required Environment Variables

Please set these environment variables in the Railway dashboard:

```bash
LANGSMITH_API_KEY=<your_langsmith_api_key>
GHL_WEBHOOK_SECRET=<your_ghl_webhook_secret>
LANGGRAPH_URL=https://ghl-python-booking-c30b52e8c48d5005b60fdf394ffbe3aa.us.langgraph.app
ASSISTANT_ID=agent
PORT=8000
```

## Instructions

1. Open the Railway dashboard: https://railway.com/project/666c7460-92e6-4d0a-878b-27edca1b6af4
2. Click on the service that was created
3. Go to the "Variables" tab
4. Add each environment variable listed above
5. The service will automatically redeploy with the new variables

## Getting the Public URL

After deployment:
1. In the Railway dashboard, go to your service
2. Click on "Settings"
3. Under "Networking", you'll find your public URL
4. It will be something like: `https://ghl-langgraph-bridge-production.up.railway.app`

## Testing the Bridge

Once deployed, test with:

```bash
# Health check
curl https://your-railway-url.railway.app/health

# Test webhook (replace with actual URL and secret)
curl -X POST https://your-railway-url.railway.app/webhook \
  -H "Content-Type: application/json" \
  -H "x-webhook-secret: your-secret" \
  -d '{
    "message": "Hi, I want to book a fitness consultation",
    "phone": "+1234567890",
    "conversationId": "test_123",
    "name": "Test User"
  }'
```