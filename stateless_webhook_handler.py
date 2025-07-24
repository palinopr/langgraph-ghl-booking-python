"""
STATELESS WEBHOOK HANDLER - Proof of Concept

This shows how to handle WhatsApp webhooks without any loops or recursion.
Each webhook is a single, independent execution.
"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage

async def stateless_webhook_handler(
    phone: str,
    message: str,
    ghl_client: Any
) -> str:
    """
    Handle a single webhook message statelessly.
    
    1. Load state from GHL
    2. Process message based on current step
    3. Save updated state to GHL
    4. Return response
    
    NO LOOPS, NO RECURSION, NO WAITING!
    """
    
    # Step 1: Get or create contact in GHL
    contact = await ghl_client.get_or_create_contact(phone)
    
    # Step 2: Read current conversation state from custom fields
    collection_step = contact.get("customFields", {}).get("collection_step", "greeting")
    language = contact.get("customFields", {}).get("language", None)
    
    # Step 3: Process THIS message based on current step
    if collection_step == "greeting":
        # First interaction
        language = detect_language(message)
        response = get_greeting_template(language)
        next_step = "name"
        
    elif collection_step == "name":
        # Extract name from message
        customer_name = extract_name(message)
        if customer_name:
            response = f"Nice to meet you {customer_name}. What are your goals?"
            next_step = "goal"
        else:
            response = "What's your name?"
            next_step = "name"  # Stay on same step
            
    elif collection_step == "goal":
        # Extract goal
        customer_goal = extract_goal(message)
        response = "What's your biggest challenge?"
        next_step = "pain"
        
    elif collection_step == "pain":
        # Extract pain point
        customer_pain = extract_pain(message)
        response = "What's your monthly marketing budget?"
        next_step = "budget"
        
    # ... continue for other steps ...
    
    # Step 4: Update GHL contact with new state
    await ghl_client.update_contact(
        contact_id=contact["id"],
        custom_fields={
            "collection_step": next_step,
            "language": language,
            # ... other fields ...
        }
    )
    
    # Step 5: Return response and END
    return response
    
    # THAT'S IT! No loops, no recursion, just:
    # Read → Process → Write → Respond → END


def detect_language(text: str) -> str:
    """Simple language detection."""
    spanish_words = ["hola", "gracias", "por favor", "ayuda"]
    return "es" if any(word in text.lower() for word in spanish_words) else "en"


def extract_name(text: str) -> str:
    """Extract name from text (simplified)."""
    # In production, use LLM or NER
    return text.strip() if len(text.split()) <= 3 else None


def extract_goal(text: str) -> str:
    """Extract business goal (simplified)."""
    return text[:50]  # First 50 chars


def extract_pain(text: str) -> str:
    """Extract pain point (simplified)."""
    return text[:50]  # First 50 chars


def get_greeting_template(language: str) -> str:
    """Get greeting in appropriate language."""
    if language == "es":
        return "¡Hola! Soy María de AI Outlet Media. ¿Cuál es tu nombre?"
    return "Hi! I'm Maria from AI Outlet Media. What's your name?"