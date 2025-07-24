# Stateless WhatsApp Booking System Architecture

## Overview
A completely stateless webhook handler where each WhatsApp message triggers an independent, atomic operation. No loops, no waiting, no recursion - just simple request/response with state persisted in GoHighLevel.

## Core Principle: One Message, One Response
```
Webhook Request → Load State → Process Message → Save State → Send Response → END
```

## GHL Custom Fields Schema

```yaml
# Conversation State
booking_step: greeting|name|goal|pain|budget|email|day|time|scheduled|complete
language: en|es

# Customer Information
customer_name: string
customer_goal: string  
customer_pain_point: string
customer_budget: number
customer_email: string
preferred_day: string
preferred_time: string

# Booking Details
appointment_id: string
appointment_datetime: datetime
booking_attempts: number
last_interaction: datetime
```

## Message Flow by Step

### Step: greeting
- **Trigger:** First message from customer
- **Process:** Detect language from message
- **Update:** Set `language` and `booking_step=name`
- **Response:** "¡Hola! Soy María de AI Outlet Media. ¿Cuál es tu nombre?"
- **Exit:** ✓

### Step: name
- **Trigger:** Message when `booking_step=name`
- **Process:** Extract name from message
- **Update:** Set `customer_name` and `booking_step=goal`
- **Response:** "Mucho gusto {name}. ¿Qué objetivos quieres lograr para tu negocio?"
- **Exit:** ✓

### Step: goal
- **Trigger:** Message when `booking_step=goal`
- **Process:** Extract business goal (max 50 chars)
- **Update:** Set `customer_goal` and `booking_step=pain`
- **Response:** "Entiendo. ¿Cuál es el mayor desafío que enfrentas actualmente?"
- **Exit:** ✓

### Step: pain
- **Trigger:** Message when `booking_step=pain`
- **Process:** Extract pain point
- **Update:** Set `customer_pain_point` and `booking_step=budget`
- **Response:** "¿Cuál es tu presupuesto mensual para marketing?"
- **Exit:** ✓

### Step: budget
- **Trigger:** Message when `booking_step=budget`
- **Process:** Extract number, validate >= $300
- **Update:** Set `customer_budget` and `booking_step=email` (or `booking_step=complete` if < $300)
- **Response:** 
  - If >= $300: "Perfecto. ¿Cuál es tu correo electrónico?"
  - If < $300: "Lo siento, trabajamos con presupuestos mínimos de $300/mes."
- **Exit:** ✓

### Step: email
- **Trigger:** Message when `booking_step=email`
- **Process:** Extract and validate email
- **Update:** Set `customer_email` and `booking_step=day`
- **Response:** "¿Qué día te gustaría agendar tu llamada? (Martes a Viernes)"
- **Exit:** ✓

### Step: day
- **Trigger:** Message when `booking_step=day`
- **Process:** Extract day, fetch available slots from GHL calendar
- **Update:** Set `preferred_day` and `booking_step=time`
- **Response:** "Tengo estos horarios disponibles para {day}: 10am, 2pm, 4pm. ¿Cuál prefieres?"
- **Exit:** ✓

### Step: time
- **Trigger:** Message when `booking_step=time`
- **Process:** Extract time, book appointment in GHL
- **Update:** Set `preferred_time`, `appointment_id`, and `booking_step=scheduled`
- **Response:** "¡Perfecto! Tu cita está confirmada para {day} a las {time}. Te envié los detalles a {email}"
- **Exit:** ✓

## Implementation Example

```python
async def handle_webhook(phone: str, message: str) -> str:
    """
    Stateless webhook handler - processes ONE message and exits.
    """
    # 1. Get or create contact
    contact = await ghl_client.get_or_create_contact(phone)
    
    # 2. Load current state
    step = contact.custom_fields.get('booking_step', 'greeting')
    language = contact.custom_fields.get('language', 'en')
    
    # 3. Process THIS message based on current step
    if step == 'greeting':
        language = detect_language(message)
        response = get_template('greeting', language)
        updates = {'language': language, 'booking_step': 'name'}
        
    elif step == 'name':
        name = extract_name(message)
        response = get_template('ask_goal', language).format(name=name)
        updates = {'customer_name': name, 'booking_step': 'goal'}
        
    # ... other steps ...
    
    # 4. Update GHL contact
    await ghl_client.update_contact_fields(contact.id, updates)
    
    # 5. Send response and END
    await ghl_client.send_message(phone, response)
    return response  # No loops, no waiting, just END
```

## Key Differences from Graph Approach

| Old (Graph/Loops) | New (Stateless) |
|-------------------|-----------------|
| Maintains conversation in memory | State stored in GHL |
| Loops waiting for responses | One response per webhook |
| Complex conditional edges | Simple if/elif by step |
| Recursion limits hit | No recursion possible |
| Stateful between messages | Completely stateless |

## Error Handling

Each step handles errors independently:
- Invalid input: Stay on same step, ask again
- GHL API error: Log and send "Please try again later"
- Missing required data: Reset to appropriate step

## Benefits

1. **No Recursion:** Impossible by design - no loops exist
2. **Scalable:** Each webhook is independent
3. **Debuggable:** Linear flow, easy to trace
4. **Resilient:** Failures don't break conversation flow
5. **Simple:** Just if/elif logic, no complex graphs

## Testing Strategy

Test each step independently:
```python
# Test name extraction
assert await handle_webhook("+1234567890", "Juan Carlos") == "Mucho gusto Juan Carlos..."

# Test budget validation  
assert await handle_webhook("+1234567890", "200") == "Lo siento, trabajamos con..."
```

No need for complex flow testing - each step is atomic!