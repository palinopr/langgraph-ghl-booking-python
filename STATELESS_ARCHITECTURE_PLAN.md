# Stateless WhatsApp Webhook Architecture

## Problem Analysis (Trace: 75b80845-b4db-4823-a7e8-6993649027b8)

The current system treats each webhook as a continuous conversation, trying to collect ALL information in a single execution:
- Input: "hola" with all fields null
- Tries to loop through: greeting → name → goal → pain → budget → email → day → time
- Hits recursion limit because it's waiting for responses that never come
- Each customer message is a NEW webhook, not a continuation

## Correct Architecture: Stateless Webhooks

### Flow for EACH Webhook:
```
1. Receive message (e.g., "hola")
2. Get phone number from webhook
3. Search GHL for existing contact
4. Read stored conversation state from contact custom fields
5. Process ONLY this message based on current step
6. Update contact with new information
7. Send ONE response
8. END (no loops, no waiting)
```

### GHL Contact Custom Fields Needed:
```json
{
  "collection_step": "name|goal|pain|budget|email|day|time|complete",
  "conversation_language": "en|es",
  "customer_goal": "string",
  "customer_pain_point": "string", 
  "customer_budget": "number",
  "preferred_day": "string",
  "preferred_time": "string",
  "booking_status": "pending|scheduled|completed"
}
```

### Example Execution Flow:

**Webhook 1:**
- Input: "hola"
- GHL lookup: No contact found
- Create contact with collection_step: "name"
- Response: "¡Hola! Soy María de AI Outlet Media. ¿Cuál es tu nombre?"
- END

**Webhook 2:**
- Input: "Juan Carlos"
- GHL lookup: Found contact, collection_step: "name"
- Update: customer_name: "Juan Carlos", collection_step: "goal"
- Response: "Mucho gusto Juan Carlos. ¿Qué objetivos quieres lograr?"
- END

**Webhook 3:**
- Input: "más clientes"
- GHL lookup: Found contact, collection_step: "goal"
- Update: customer_goal: "más clientes", collection_step: "pain"
- Response: "¿Cuál es tu mayor desafío actualmente?"
- END

### Key Changes Required:

1. **Remove LangGraph workflow loops**
   - No conditional edges that loop back
   - Single linear execution per webhook

2. **Add GHL persistence layer**
   - Extend GHLClient with update_contact_fields()
   - Store all conversation state in GHL

3. **Simplify webhook handler**
   - Load state from GHL
   - Process single message
   - Save state to GHL
   - Return single response

4. **No recursion possible**
   - Each webhook is independent
   - No loops, no waiting
   - Maximum 1 input → 1 output

This architecture completely eliminates recursion issues because there's no looping - just discrete, stateless message processing!