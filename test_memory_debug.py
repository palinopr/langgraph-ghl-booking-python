#!/usr/bin/env python3
"""Debug conversation memory."""

import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()

# Enable debug logging
logging.basicConfig(level=logging.INFO)

from stateless_booking.ghl_state_manager import GHLStateManager


async def debug_conversation_history():
    """Debug the conversation history retrieval."""
    
    print("🔍 Debugging Conversation History")
    print("=" * 50)
    
    ghl = GHLStateManager()
    
    # Test with a known contact
    test_phone = "+1234567890"
    
    # Get or create contact
    print(f"\n1. Getting contact for {test_phone}")
    contact = await ghl.get_or_create_contact(test_phone)
    print(f"Contact ID: {contact.get('id')}")
    
    # Try to get conversation history
    print(f"\n2. Getting conversation history")
    history = await ghl.get_conversation_history(contact["id"])
    print(f"History length: {len(history)}")
    
    if history:
        print("\nConversation history:")
        for i, msg in enumerate(history):
            print(f"  {i+1}. [{msg['role']}]: {msg['content'][:50]}...")
    else:
        print("No history found - this might be why memory isn't working!")
    
    # Send a test message to create history
    print(f"\n3. Sending test message")
    success = await ghl.send_message(contact["id"], "Test message from memory debug", "SMS")
    print(f"Message sent: {success}")
    
    # Try again after sending
    print(f"\n4. Getting history after sending message")
    history2 = await ghl.get_conversation_history(contact["id"])
    print(f"History length after send: {len(history2)}")


if __name__ == "__main__":
    asyncio.run(debug_conversation_history())