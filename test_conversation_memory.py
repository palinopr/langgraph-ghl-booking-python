#!/usr/bin/env python3
"""Test conversation memory implementation."""

import asyncio
from dotenv import load_dotenv
load_dotenv()

from stateless_booking.webhook_handler import handle_webhook_message


async def test_conversation_memory():
    """Test that AI remembers previous messages."""
    
    print("🧪 Testing Conversation Memory")
    print("=" * 50)
    
    # Use a consistent phone number for testing
    test_phone = "+1234567891"  # Different from previous tests
    
    # Test 1: Send name
    print("\n📋 Test 1: Sending Name")
    result1 = await handle_webhook_message({
        "phone": test_phone,
        "message": "My name is Rachel Chen"
    })
    print(f"Customer: My name is Rachel Chen")
    print(f"AI Response: {result1['message']}")
    
    # Test 2: Ask if AI remembers
    print("\n📋 Test 2: Testing Memory")
    result2 = await handle_webhook_message({
        "phone": test_phone,
        "message": "What did I just tell you?"
    })
    print(f"Customer: What did I just tell you?")
    print(f"AI Response: {result2['message']}")
    print(f"Memory works: {'Rachel' in result2['message'] or 'name' in result2['message'].lower()}")
    
    # Test 3: Continue conversation
    print("\n📋 Test 3: Continue with Context")
    result3 = await handle_webhook_message({
        "phone": test_phone,
        "message": "I need help with marketing automation"
    })
    print(f"Customer: I need help with marketing automation")
    print(f"AI Response: {result3['message']}")
    print(f"Uses name: {'Rachel' in result3['message']}")
    
    # Test 4: Test memory limit
    print("\n📋 Test 4: Memory After Multiple Messages")
    result4 = await handle_webhook_message({
        "phone": test_phone,
        "message": "Do you remember my name?"
    })
    print(f"Customer: Do you remember my name?")
    print(f"AI Response: {result4['message']}")
    print(f"Still remembers: {'Rachel' in result4['message']}")
    
    print("\n" + "=" * 50)
    print("✅ Conversation Memory Test Complete")


if __name__ == "__main__":
    asyncio.run(test_conversation_memory())