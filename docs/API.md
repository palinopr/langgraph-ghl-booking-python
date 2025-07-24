# API Reference

## Overview

The WhatsApp Booking System exposes a FastAPI-based webhook server that receives messages from WhatsApp (via GoHighLevel) and processes them through a LangGraph workflow to automatically book appointments.

## Base URL

```
Production: https://your-domain.com
Development: http://localhost:8000
```

## Authentication

All webhook requests must include a valid signature in the `X-GHL-Signature` header for security. The signature is computed using HMAC-SHA256 with your webhook secret.

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Endpoints

### 1. Webhook Handler

Receives and processes WhatsApp messages.

**Endpoint:** `POST /webhook`

**Headers:**
- `Content-Type: application/json`
- `X-GHL-Signature: <webhook-signature>`

**Request Body:**
```json
{
  "type": "message",
  "contactId": "contact_123",
  "locationId": "loc_abc123",
  "conversationId": "conv_456",
  "message": {
    "id": "msg_789",
    "body": "Hi, I need help with marketing. My budget is $2000",
    "from": "+1234567890",
    "to": "+0987654321",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "contact": {
    "id": "contact_123",
    "name": "John Doe",
    "phone": "+1234567890",
    "email": "john@example.com"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Message processed successfully",
  "booking_id": "book_xyz789",
  "workflow_run_id": "run_abc123"
}
```

**Status Codes:**
- `200 OK` - Message processed successfully
- `400 Bad Request` - Invalid request format
- `401 Unauthorized` - Invalid signature
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Processing error

**Rate Limiting:**
- 30 requests per minute per IP address
- 100 requests per minute per phone number

### 2. Health Check

Check if the service is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": "connected",
    "ghl_api": "connected",
    "openai_api": "connected"
  }
}
```

### 3. System Status

Get detailed system status and metrics.

**Endpoint:** `GET /status`

**Response:**
```json
{
  "status": "operational",
  "uptime": 3600,
  "processed_messages": 1234,
  "successful_bookings": 1000,
  "failed_bookings": 34,
  "average_processing_time": 2.5,
  "queue_length": 5,
  "last_error": null,
  "version": {
    "api": "1.0.0",
    "langgraph": "0.3.27",
    "python": "3.11.0"
  }
}
```

### 4. Metrics (Prometheus)

Expose metrics in Prometheus format.

**Endpoint:** `GET /metrics`

**Response:**
```
# HELP webhook_requests_total Total number of webhook requests
# TYPE webhook_requests_total counter
webhook_requests_total{status="success"} 1000
webhook_requests_total{status="error"} 34

# HELP booking_duration_seconds Time taken to process bookings
# TYPE booking_duration_seconds histogram
booking_duration_seconds_bucket{le="0.5"} 100
booking_duration_seconds_bucket{le="1.0"} 800
booking_duration_seconds_bucket{le="2.0"} 950
booking_duration_seconds_bucket{le="5.0"} 1000
booking_duration_seconds_bucket{le="+Inf"} 1000

# HELP active_workflows Number of active workflows
# TYPE active_workflows gauge
active_workflows 5
```

## Webhook Event Types

### 1. Incoming Message

Standard WhatsApp message from a customer.

```json
{
  "type": "message",
  "message": {
    "body": "User message text",
    "from": "+1234567890"
  }
}
```

### 2. Message Status Update

Updates on message delivery status.

```json
{
  "type": "message_status",
  "status": "delivered",
  "messageId": "msg_123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Appointment Confirmation

Confirmation that an appointment was booked.

```json
{
  "type": "appointment_confirmed",
  "appointmentId": "apt_456",
  "scheduledTime": "2024-01-20T14:00:00Z",
  "contactId": "contact_123"
}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "details": {
      "field": "message.from",
      "value": "invalid-phone"
    },
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `UNAUTHORIZED` | Invalid or missing signature | 401 |
| `RATE_LIMITED` | Too many requests | 429 |
| `WORKFLOW_ERROR` | Error in workflow processing | 500 |
| `GHL_API_ERROR` | GoHighLevel API error | 502 |
| `TIMEOUT` | Request processing timeout | 504 |

## Workflow Integration

### Workflow States

The webhook triggers a LangGraph workflow with the following states:

1. **Triage** - Filter spam and irrelevant messages
2. **Collection** - Extract customer information
3. **Validation** - Check business rules
4. **Booking** - Create appointment in GHL

### Workflow Response

After processing, the workflow returns:

```json
{
  "workflow_run_id": "run_123",
  "final_state": "completed",
  "nodes_executed": ["triage", "collect", "validate", "book"],
  "result": {
    "booking_created": true,
    "appointment_id": "apt_789",
    "scheduled_time": "2024-01-20T14:00:00Z",
    "customer": {
      "name": "John Doe",
      "goal": "Marketing help",
      "budget": 2000
    }
  },
  "execution_time": 2.5
}
```

## Testing

### Test Webhook Locally

```bash
# Basic test
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GHL-Signature: test-signature" \
  -d '{
    "type": "message",
    "message": {
      "body": "I need help with marketing. Budget is $2000",
      "from": "+1234567890"
    }
  }'

# Test with full payload
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GHL-Signature: test-signature" \
  -d @test-payload.json
```

### Generate Test Signature

```python
import hmac
import hashlib
import json

def generate_test_signature(payload: dict, secret: str) -> str:
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
    return hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

# Example
payload = {"type": "message", "message": {"body": "Test"}}
secret = "your-webhook-secret"
signature = generate_test_signature(payload, secret)
print(f"X-GHL-Signature: {signature}")
```

## Best Practices

### 1. Webhook Security
- Always validate signatures
- Use HTTPS in production
- Rotate webhook secrets regularly
- Log all requests for audit

### 2. Error Handling
- Implement retry logic for transient failures
- Use exponential backoff
- Set reasonable timeouts (30s recommended)
- Return appropriate status codes

### 3. Performance
- Process messages asynchronously
- Implement request queuing for high load
- Use connection pooling for external APIs
- Monitor response times

### 4. Monitoring
- Track success/failure rates
- Monitor response times
- Set up alerts for errors
- Use distributed tracing

## SDK Examples

### Python Client

```python
import httpx
import hmac
import hashlib
import json

class BookingWebhookClient:
    def __init__(self, base_url: str, webhook_secret: str):
        self.base_url = base_url
        self.webhook_secret = webhook_secret
        self.client = httpx.AsyncClient()
    
    def _generate_signature(self, payload: dict) -> str:
        payload_bytes = json.dumps(payload).encode()
        return hmac.new(
            self.webhook_secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
    
    async def send_message(self, message: str, phone: str) -> dict:
        payload = {
            "type": "message",
            "message": {
                "body": message,
                "from": phone
            }
        }
        
        signature = self._generate_signature(payload)
        
        response = await self.client.post(
            f"{self.base_url}/webhook",
            json=payload,
            headers={
                "X-GHL-Signature": signature
            }
        )
        
        response.raise_for_status()
        return response.json()

# Usage
client = BookingWebhookClient(
    base_url="https://api.example.com",
    webhook_secret="your-secret"
)

result = await client.send_message(
    message="I need marketing help. Budget $2000",
    phone="+1234567890"
)
```

### JavaScript/Node.js Client

```javascript
const crypto = require('crypto');
const axios = require('axios');

class BookingWebhookClient {
  constructor(baseUrl, webhookSecret) {
    this.baseUrl = baseUrl;
    this.webhookSecret = webhookSecret;
  }

  generateSignature(payload) {
    return crypto
      .createHmac('sha256', this.webhookSecret)
      .update(JSON.stringify(payload))
      .digest('hex');
  }

  async sendMessage(message, phone) {
    const payload = {
      type: 'message',
      message: {
        body: message,
        from: phone
      }
    };

    const signature = this.generateSignature(payload);

    const response = await axios.post(
      `${this.baseUrl}/webhook`,
      payload,
      {
        headers: {
          'Content-Type': 'application/json',
          'X-GHL-Signature': signature
        }
      }
    );

    return response.data;
  }
}

// Usage
const client = new BookingWebhookClient(
  'https://api.example.com',
  'your-secret'
);

const result = await client.sendMessage(
  'I need marketing help. Budget $2000',
  '+1234567890'
);
```

## Postman Collection

Import this collection to test the API:

```json
{
  "info": {
    "name": "WhatsApp Booking API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Send Message",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "X-GHL-Signature",
            "value": "{{signature}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"type\": \"message\",\n  \"message\": {\n    \"body\": \"I need help with marketing. Budget $2000\",\n    \"from\": \"+1234567890\"\n  }\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/webhook",
          "host": ["{{baseUrl}}"],
          "path": ["webhook"]
        }
      }
    },
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{baseUrl}}/health",
          "host": ["{{baseUrl}}"],
          "path": ["health"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000"
    },
    {
      "key": "signature",
      "value": "generate-this-value"
    }
  ]
}
```

---

For more information, see the [main documentation](../README.md) or [deployment guide](DEPLOYMENT.md).