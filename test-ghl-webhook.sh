#!/bin/bash

# Test GHL webhook request locally
echo "Testing GHL webhook with authentication..."

# Set the webhook secret (use environment variable or default)
WEBHOOK_SECRET="${GHL_WEBHOOK_SECRET:-test-webhook-secret}"

# Send test webhook request
curl -X POST http://localhost:3000/webhook \
  -H "Content-Type: application/json" \
  -H "x-webhook-secret: ${WEBHOOK_SECRET}" \
  -d '{
    "message": "Hi, I want to book a fitness consultation. My budget is $2000/month and I want to lose weight.",
    "phone": "+1234567890",
    "conversationId": "conv_ghl_test_001",
    "type": "InboundMessage",
    "locationId": "'${GHL_LOCATION_ID:-loc_test}'",
    "contactId": "contact_test_001",
    "name": "Rachel Test User",
    "email": "rachel.test@example.com",
    "messageType": "WhatsApp",
    "direction": "inbound",
    "dateAdded": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }' | jq .

echo -e "\n\nChecking server logs..."
tail -n 20 webhook.log 2>/dev/null || echo "No webhook logs found"