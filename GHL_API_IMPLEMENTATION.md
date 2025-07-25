# 🔥 GHL API IMPLEMENTATION - CORRECT ENDPOINTS

Based on the official GoHighLevel API documentation, here's the CORRECT implementation:

## 🚨 CRITICAL FIX #1: Message Sending

### WRONG (What we have):
```python
async def send_message(self, phone: str, message: str) -> bool:
    """Send message via GHL (placeholder - implement based on GHL SMS/WhatsApp API)."""
    logger.info(f"Sending to {phone}: {message}")
    return True  # NOT SENDING!
```

### CORRECT Implementation:
```python
async def send_message(self, contact_id: str, message: str, message_type: str = "SMS") -> bool:
    """Send message via GHL Conversations API"""
    async with aiohttp.ClientSession() as session:
        # API Endpoint: POST /conversations/messages
        url = f"{self.base_url}/conversations/messages"
        
        # Correct payload structure from docs
        body = {
            "type": message_type,  # "SMS" or "WhatsApp"
            "contactId": contact_id,
            "message": message,
            "attachments": []  # Optional attachments
        }
        
        async with session.post(url, headers=self.headers, json=body) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                logger.info(f"Message sent: {data.get('messageId')}")
                return True
            else:
                error = await resp.text()
                logger.error(f"Failed to send: {resp.status} - {error}")
                return False
```

## 🔍 CRITICAL FIX #2: Get Conversation History

### Correct Search Endpoint:
```python
async def get_conversation_history(self, contact_id: str) -> List[Dict[str, Any]]:
    """Get conversation history for AI context"""
    async with aiohttp.ClientSession() as session:
        # Search for conversations by contact
        # API Endpoint: GET /conversations/search
        search_url = f"{self.base_url}/conversations/search"
        params = {
            "locationId": self.location_id,
            "contactId": contact_id
        }
        
        async with session.get(search_url, headers=self.headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                conversations = data.get("conversations", [])
                
                # Get the active conversation
                if conversations:
                    conv_id = conversations[0].get("id")
                    return await self._get_messages(conv_id)
            return []
    
async def _get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
    """Get messages for a conversation"""
    # NOTE: The exact endpoint for getting messages is not clearly documented
    # It might be part of the conversation object or require a separate call
    # Need to test with actual API
    pass
```

## 📱 WhatsApp-Specific Implementation

Based on the webhook examples, WhatsApp messages follow this structure:

### Incoming WhatsApp Message (from webhook):
```json
{
  "type": "InboundMessage",
  "locationId": "your_location_id",
  "body": "Customer message text",
  "contactId": "contact_id",
  "conversationId": "conversation_id",
  "messageType": "SMS",  // Even WhatsApp shows as SMS in examples
  "direction": "inbound",
  "conversationProviderId": "provider_id"
}
```

### Sending WhatsApp Message:
```python
async def send_whatsapp_message(self, contact_id: str, message: str) -> bool:
    """Send WhatsApp message via GHL"""
    return await self.send_message(
        contact_id=contact_id,
        message=message,
        message_type="WhatsApp"  # Specify WhatsApp type
    )
```

## 🎯 Complete Working Implementation

```python
class GHLMessagingManager:
    """Handles all GHL messaging operations"""
    
    def __init__(self):
        self.api_key = os.getenv("GHL_API_KEY")
        self.location_id = os.getenv("GHL_LOCATION_ID")
        self.base_url = "https://services.leadconnectorhq.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
    
    async def process_inbound_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming WhatsApp message from webhook"""
        # Extract from webhook
        contact_id = webhook_data.get("contactId")
        message = webhook_data.get("body")
        conversation_id = webhook_data.get("conversationId")
        
        # Process with AI
        ai_response = await self.ai_engine.process(
            message=message,
            contact_id=contact_id,
            conversation_id=conversation_id
        )
        
        # Send response
        await self.send_message(
            contact_id=contact_id,
            message=ai_response["message"],
            message_type="SMS"  # or "WhatsApp"
        )
        
        return {
            "status": "processed",
            "ai_notes": ai_response["notes"]
        }
    
    async def send_message(self, contact_id: str, message: str, message_type: str = "SMS") -> Dict[str, Any]:
        """Send message through GHL Conversations API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/conversations/messages"
            
            body = {
                "type": message_type,
                "contactId": contact_id, 
                "message": message,
                "attachments": []
            }
            
            # Add location ID header if needed
            headers = self.headers.copy()
            headers["Location-Id"] = self.location_id
            
            async with session.post(url, headers=headers, json=body) as resp:
                response_data = await resp.json()
                
                if resp.status in [200, 201]:
                    return {
                        "success": True,
                        "messageId": response_data.get("messageId"),
                        "conversationId": response_data.get("conversationId")
                    }
                else:
                    logger.error(f"Send failed: {response_data}")
                    return {
                        "success": False,
                        "error": response_data
                    }
```

## ⚠️ Important Notes from Documentation

1. **Message Types**: Use "SMS" or "WhatsApp" in the type field
2. **Contact ID Required**: You MUST have the contact ID, not just phone number
3. **Location ID**: May need to be passed in headers or params
4. **Webhook Format**: InboundMessage and OutboundMessage have specific schemas
5. **No Direct Phone Send**: API requires contactId, not phone number

## 🔧 Required Updates to Our System

1. **Update webhook handler** to extract contactId from webhook
2. **Store contactId** in our state management
3. **Use correct endpoints** for sending messages
4. **Handle conversation context** properly

## 📝 Next Steps

1. Test the `/conversations/messages` endpoint with real credentials
2. Verify WhatsApp message type works
3. Find the exact endpoint for retrieving message history
4. Update our stateless handler to use these correct endpoints