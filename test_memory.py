#!/usr/bin/env python3
"""
Test AI conversation memory - ensures AI remembers previous messages.
"""
import os
from dotenv import load_dotenv
from stateless_booking.message_processor import MessageProcessor

# Load environment
load_dotenv()


async def test_conversation_memory():
    """Test that AI remembers names from previous messages."""
    processor = MessageProcessor()
    
    print("🧠 AI MEMORY TEST")
    print("=" * 60)
    
    # Simulate conversation history where customer said "I'm John"
    conversation_history = [
        {"role": "ai", "content": "Hello! Welcome to AI Outlet Media. What's your name?"},
        {"role": "customer", "content": "I'm John"},
        {"role": "ai", "content": "Nice to meet you John! What specific goals are you looking to achieve with AI automation?"}
    ]
    
    # Customer state with name stored
    state = {
        "customer_name": "John",
        "booking_step": "goal",
        "language": "en"
    }
    
    # Test 1: Customer asks "What's my name?"
    print("\n✅ TEST 1: Memory Recall")
    print("Previous conversation:")
    for msg in conversation_history:
        print(f"  {msg['role'].upper()}: {msg['content']}")
    
    print("\nNew message:")
    result = await processor.process_message(
        "What's my name?", 
        "goal", 
        "en", 
        state,
        conversation_history
    )
    
    print(f"Customer: What's my name?")
    print(f"AI: {result['response']}")
    
    # Check if AI mentions "John" in response
    if "John" in result['response']:
        print("✅ PASS: AI remembered the name John!")
    else:
        print("❌ FAIL: AI didn't remember the name")
    
    # Test 2: Continue conversation about automation
    print("\n✅ TEST 2: Context Continuation")
    conversation_history.extend([
        {"role": "customer", "content": "What's my name?"},
        {"role": "ai", "content": result['response']}
    ])
    
    result2 = await processor.process_message(
        "I want to automate my customer service",
        "goal",
        "en",
        state,
        conversation_history
    )
    
    print(f"Customer: I want to automate my customer service")
    print(f"AI: {result2['response']}")
    
    # Test 3: Without conversation history (should not remember)
    print("\n✅ TEST 3: Without History (Control)")
    result3 = await processor.process_message(
        "What's my name?",
        "greeting",
        "en",
        {},  # Empty state
        []   # Empty history
    )
    
    print(f"Customer: What's my name?")
    print(f"AI: {result3['response']}")
    
    if "John" not in result3['response']:
        print("✅ PASS: AI correctly doesn't know name without history")
    else:
        print("❌ FAIL: AI shouldn't know name without history")
    
    print("\n" + "=" * 60)
    print("🎉 MEMORY TEST COMPLETE!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_conversation_memory())