# FastAPI Webhook Server

David Kim reporting: Production-ready webhook server for WhatsApp booking system.

## Features

- ✅ FastAPI with async support
- ✅ Rate limiting (30 requests/minute)
- ✅ Webhook signature verification
- ✅ Health check endpoints
- ✅ Comprehensive error handling
- ✅ Structured logging
- ✅ Pydantic models for validation

## API Endpoints

### POST /webhook
Receives WhatsApp messages and processes them through the booking workflow.

```json
{
  "message": "Hi, I want to book an appointment",
  "phone": "+1234567890",
  "thread_id": "unique_thread_id",
  "signature": "optional_signature"
}
```

### GET /health
Health check endpoint for monitoring.

Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### GET /metrics
Server metrics for monitoring.

Response:
```json
{
  "requests": 100,
  "errors": 2,
  "rate_limited": 5,
  "active_threads": 3,
  "uptime_seconds": 3600.0,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Security Features

1. **Rate Limiting**: Prevents abuse with 30 requests/minute limit
2. **Signature Verification**: Optional webhook signature validation
3. **Error Handling**: Consistent error responses
4. **Request Logging**: All requests are logged for debugging

## Running the Server

### Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m api.webhook
```

### Production Mode
```bash
# Using uvicorn directly
uvicorn api.webhook:app --host 0.0.0.0 --port 3000
```

### Testing
```bash
# Run the test script
python scripts/test_api.py
```

## Integration with Workflow

The webhook server automatically integrates with Sofia's workflow when available:

1. Webhook receives message
2. Validates and rate limits request
3. Passes to workflow for processing
4. Returns acknowledgment to sender

If the workflow is not available, the server runs in API-only mode and acknowledges receipt.

## Environment Variables

See `.env.example` for required configuration:
- `PORT`: Server port (default: 3000)
- `GHL_WEBHOOK_SECRET`: Optional signature verification
- `LOG_LEVEL`: Logging level (default: INFO)

## Error Responses

All errors follow a consistent format:
```json
{
  "error": "error_type",
  "message": "Human readable message",
  "details": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Next Steps

1. Sofia will create the workflow in `booking_agent/`
2. David (me) will integrate with the workflow
3. Marcus will add comprehensive tests
4. Sarah will set up Docker deployment