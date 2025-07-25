# 🚨 CRITICAL API IMPLEMENTATION PLAN

## Priority 1: GHL WhatsApp Message Sending (NOTHING WORKS WITHOUT THIS!)

### Current Problem
```python
async def send_message(self, phone: str, message: str) -> bool:
    """Send message via GHL (placeholder - implement based on GHL SMS/WhatsApp API)."""
    # In production, this would send via GHL's messaging API
    logger.info(f"Sending to {phone}: {message}")
    return True  # NOT ACTUALLY SENDING!
```

### Required Implementation
```python
async def send_message(self, phone: str, message: str) -> bool:
    """Send WhatsApp message via GHL Conversations API"""
    async with aiohttp.ClientSession() as session:
        # Step 1: Get or create conversation
        conversation_url = f"{self.base_url}/conversations"
        conversation_body = {
            "locationId": self.location_id,
            "contactId": contact_id,  # Need to pass this
            "type": "WhatsApp"
        }
        
        # Step 2: Send message
        message_url = f"{self.base_url}/conversations/messages"
        message_body = {
            "conversationId": conversation_id,
            "type": "WhatsApp", 
            "message": {
                "type": "text",
                "text": message
            }
        }
        
        async with session.post(message_url, headers=self.headers, json=message_body) as resp:
            if resp.status in [200, 201]:
                logger.info(f"Message sent successfully to {phone}")
                return True
            else:
                error = await resp.text()
                logger.error(f"Failed to send message: {error}")
                return False
```

### GHL API Endpoints Needed
1. `POST /conversations` - Create/get conversation
2. `POST /conversations/messages` - Send message
3. `GET /conversations/messages` - Get conversation history

## Priority 2: GHL Conversation History API

### Why It's Critical
- AI needs full context to respond intelligently
- Can't make smart decisions without knowing what was already discussed
- Prevents asking for information already provided

### Implementation
```python
class GHLConversationManager:
    """Manages conversation history for AI context"""
    
    async def get_conversation_history(
        self, 
        contact_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for AI context"""
        async with aiohttp.ClientSession() as session:
            # Get conversations for contact
            search_url = f"{self.base_url}/conversations/search"
            params = {
                "locationId": self.location_id,
                "contactId": contact_id,
                "type": "WhatsApp",
                "limit": limit
            }
            
            async with session.get(search_url, headers=self.headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    conversations = data.get("conversations", [])
                    
                    # Get messages for each conversation
                    all_messages = []
                    for conv in conversations:
                        messages = await self._get_conversation_messages(conv["id"])
                        all_messages.extend(messages)
                    
                    # Sort by timestamp
                    return sorted(all_messages, key=lambda x: x["dateAdded"])
                    
    async def _get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get messages for a specific conversation"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/conversations/{conversation_id}/messages"
            params = {"limit": 100}
            
            async with session.get(url, headers=self.headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("messages", [])
                return []
```

## Priority 3: Enhanced State Storage

### Current Limitation
We only have basic fields. AI needs rich storage:

### Required Custom Fields
```python
AI_CUSTOM_FIELDS = {
    # Conversation Intelligence (NEW)
    "ai_notes": {
        "name": "AI Conversation Notes",
        "type": "LARGE_TEXT",  # Up to 5000 chars
        "description": "Complete AI notes from conversation"
    },
    "ai_insights": {
        "name": "AI Customer Insights", 
        "type": "LARGE_TEXT",
        "description": "Personality, preferences, behavior patterns"
    },
    "ai_context": {
        "name": "AI Full Context",
        "type": "LARGE_TEXT", 
        "description": "Complete conversation state as JSON"
    },
    "ai_qualification": {
        "name": "AI Qualification Score",
        "type": "NUMBER",
        "description": "1-10 score of lead quality"
    },
    "ai_next_action": {
        "name": "AI Recommended Action",
        "type": "TEXT",
        "description": "What AI recommends doing next"
    }
}
```

## Priority 4: OpenAI Integration

### Simple Integration First
```python
from openai import AsyncOpenAI

class SimpleAIEngine:
    """Basic AI engine for MVP"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def generate_response(
        self,
        customer_message: str,
        conversation_history: List[str],
        customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI response with notes"""
        
        # Build context
        context = f"""
        Customer Info: {json.dumps(customer_info)}
        
        Conversation History:
        {chr(10).join(conversation_history[-10:])}  # Last 10 messages
        
        Current Message: {customer_message}
        """
        
        # Generate response
        completion = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content)
```

## 🚀 Implementation Order

### Day 1-2: Message Sending
1. Research exact GHL Conversations API format
2. Implement send_message properly
3. Test with real WhatsApp messages
4. Handle errors gracefully

### Day 3-4: Conversation History
1. Implement conversation search
2. Implement message retrieval
3. Format for AI consumption
4. Test with real conversations

### Day 5: State Storage
1. Create all AI custom fields in GHL
2. Update field mapping
3. Implement JSON storage for complex data
4. Test state persistence

### Day 6-7: Basic AI Integration
1. Set up OpenAI client
2. Create system prompt
3. Implement response generation
4. Add note-taking
5. Test AI responses

### Week 2: Full Integration
1. Connect all components
2. Implement intelligent routing
3. Add qualification scoring
4. Deploy and monitor

## ⚠️ Blocking Issues to Resolve

1. **GHL API Documentation**: Need exact endpoints and formats
2. **WhatsApp Integration**: Verify GHL location has WhatsApp enabled
3. **API Rate Limits**: Understand GHL's rate limiting
4. **Message Formatting**: WhatsApp has specific format requirements
5. **Webhook Updates**: May need different webhook format for conversations

## 🔑 Required Information from GHL

```bash
# Test these endpoints with curl
curl -X GET "https://services.leadconnectorhq.com/conversations/search" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Version: 2021-07-28" \
  -d "locationId=YOUR_LOCATION_ID"

# We need to verify:
1. Exact conversation API endpoints
2. Message sending format
3. WhatsApp-specific requirements
4. Rate limits and quotas
5. Webhook payload format for conversations
```

Without implementing these APIs, we're just building a fancy bot that can't actually communicate!