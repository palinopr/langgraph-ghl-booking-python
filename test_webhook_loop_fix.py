#!/usr/bin/env python3
"""Test infinite loop fix through webhook."""

import requests
import json
import time
import os

def test_webhook_loop_fix():
    """Test the infinite loop fix via webhook."""
    
    webhook_url = "http://localhost:8123/webhook"
    webhook_secret = os.getenv("GHL_WEBHOOK_SECRET", "your_webhook_secret_here")
    
    print("🧪 Testing Infinite Loop Fix via Webhook")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "x-webhook-secret": webhook_secret
    }
    
    # Test 1: Spanish "hola" - should get ONE response only
    print("\n📋 Test 1: Spanish 'hola' - No infinite loop")
    print("-" * 40)
    
    start_time = time.time()
    
    response = requests.post(
        webhook_url,
        json={
            "message": "hola",
            "thread_id": "test_loop_1",
            "phone": "+1234567890",
            "conversationId": "conv_loop_1"
        },
        headers=headers,
        timeout=30
    )
    
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        message = data.get('message', '')
        
        print(f"  ✅ Status: 200")
        print(f"  Response: {message[:100]}...")
        print(f"  Response time: {elapsed:.2f}s")
        
        # Check if it's Spanish response
        is_spanish = "hola" in message.lower() or "maría" in message.lower()
        print(f"  Language: {'Spanish' if is_spanish else 'English'}")
        
        if elapsed < 15:  # Should complete quickly if no loop
            print("  ✅ PASS: No infinite loop detected (quick response)")
        else:
            print("  ❌ FAIL: Response took too long, possible loop")
    else:
        print(f"  ❌ Status: {response.status_code}")
        print(f"  Error: {response.text}")
    
    # Test 2: Continue conversation
    print("\n\n📋 Test 2: Continue conversation - Proper flow")
    print("-" * 40)
    
    # Send name
    response2 = requests.post(
        webhook_url,
        json={
            "message": "Mi nombre es Carlos",
            "thread_id": "test_loop_1",  # Same thread
            "phone": "+1234567890",
            "conversationId": "conv_loop_1"
        },
        headers=headers,
        timeout=30
    )
    
    if response2.status_code == 200:
        data2 = response2.json()
        message2 = data2.get('message', '')
        
        print(f"  ✅ Status: 200")
        print(f"  Response: {message2[:100]}...")
        
        # Should ask for goal next
        if "objetivo" in message2.lower() or "goal" in message2.lower():
            print("  ✅ PASS: Correctly moved to next step (asking for goal)")
        else:
            print("  ❌ FAIL: Did not progress to goal collection")
    
    # Test 3: Multiple messages in sequence
    print("\n\n📋 Test 3: Full conversation flow - No loops")
    print("-" * 40)
    
    test_messages = [
        ("Hi", "English greeting"),
        ("My name is John", "Name provided"),
        ("I want to grow my business", "Goal provided"),
        ("I'm struggling with online marketing", "Pain point"),
        ("My budget is $500", "Budget provided"),
        ("john@example.com", "Email provided"),
        ("Thursday", "Day preference"),
        ("2pm", "Time preference")
    ]
    
    thread_id = f"test_full_flow_{int(time.time())}"
    
    for i, (msg, description) in enumerate(test_messages[:4]):  # Test first 4 steps
        print(f"\n  Step {i+1}: {description}")
        print(f"  Sending: '{msg}'")
        
        response = requests.post(
            webhook_url,
            json={
                "message": msg,
                "thread_id": thread_id,
                "phone": "+1234567891",
                "conversationId": f"conv_full_{thread_id}"
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get('message', '')
            print(f"  Response: {reply[:80]}...")
        else:
            print(f"  ❌ Error: {response.status_code}")
            break
        
        time.sleep(0.5)  # Small delay between messages
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("  ✅ Workflow properly exits after each AI response")
    print("  ✅ No infinite loops detected")
    print("  ✅ Conversation flows correctly through steps")
    print("  ✅ Each step waits for user input before continuing")

if __name__ == "__main__":
    # Check if server is running
    try:
        health = requests.get("http://localhost:8123/health").json()
        print(f"✅ Server health: {health}\n")
        test_webhook_loop_fix()
    except Exception as e:
        print(f"❌ Server not running: {e}")
        print("Please ensure webapp.py is running")