"""
Stateless webhook handler - processes ONE message and exits.
NO LOOPS, NO RECURSION, NO WAITING.
"""
import os
import logging
from typing import Dict, Any
from datetime import datetime
from langsmith import traceable

from .ghl_state_manager import GHLStateManager
from .message_processor import MessageProcessor
from .message_storage import MessageStorage

logger = logging.getLogger(__name__)


@traceable(name="process_webhook_core", run_type="chain")
async def _process_webhook_core(phone: str, message: str, ghl: GHLStateManager, 
                               processor: MessageProcessor, storage: MessageStorage) -> Dict[str, Any]:
    """Core webhook processing logic - extracted to keep functions under 40 lines."""
    # Get or create contact and load state
    contact = await ghl.get_or_create_contact(phone)
    state = await ghl.get_conversation_state(contact["id"])
    
    # Save incoming message to local storage
    await storage.save_message(contact["id"], {
        "role": "customer",
        "content": message,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Get conversation history from local storage
    conversation_history = await storage.get_messages(contact["id"], limit=10)
    
    # Process THIS message only
    current_step = state.get("booking_step", "greeting")
    language = state.get("language", "en")
    
    # Pass conversation history to processor
    result = await processor.process_message(
        message, current_step, language, state, conversation_history
    )
    next_step = result["next_step"]
    updates = result["updates"]
    response = result["response"]
    
    # Update state in GHL
    updates["booking_step"] = next_step
    updates["last_interaction"] = "now"  # GHL will use current timestamp
    await ghl.update_conversation_state(contact["id"], updates)
    
    # Save AI response to local storage
    await storage.save_message(contact["id"], {
        "role": "ai",
        "content": response,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Send response and EXIT - NO LOOPS!
    await ghl.send_message(contact["id"], response, "WhatsApp")  # Use contact ID, not phone
    
    return {
        "status": "success",
        "message": response,
        "step": next_step
    }


@traceable(name="handle_webhook_message", run_type="chain")
async def handle_webhook_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a single webhook message atomically.
    
    Args:
        data: Webhook data containing phone and message
        
    Returns:
        Response dict with status and message
        
    NO LOOPS - just process and exit!
    """
    try:
        # Extract webhook data
        phone = data.get("phone", "").strip()
        message = data.get("message", "").strip()
        
        if not phone or not message:
            return {"status": "error", "message": "Missing phone or message"}
        
        # Initialize managers
        ghl = GHLStateManager()
        processor = MessageProcessor()
        storage = MessageStorage()
        
        # Delegate to core processing
        return await _process_webhook_core(phone, message, ghl, processor, storage)
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return {
            "status": "error", 
            "message": "An error occurred. Please try again."
        }

# That's it! No loops, no recursion, just simple processing!