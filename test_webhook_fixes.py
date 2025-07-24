#!/usr/bin/env python3
"""Test both fixes: language detection and ainvoke."""

import requests
import json
import time
import os

def test_webhook_fixes():
    webhook_url = "http://localhost:8123/webhook"
    webhook_secret = os.getenv("GHL_WEBHOOK_SECRET", "your_webhook_secret_here")
    
    print("🧪 Testing Critical Bug Fixes\n")
    
    # Test cases focusing on the fixes
    test_cases = [
        {
            "name": "Language Detection: Single 'hola'",
            "payload": {
                "message": "hola",
                "thread_id": "test_lang_1",
                "phone": "+1234567890"
            },
            "expected_language": "Spanish response expected"
        },
        {
            "name": "Language Detection: English with Spanish word",
            "payload": {
                "message": "I said hola to my friend",
                "thread_id": "test_lang_2", 
                "phone": "+1234567891"
            },
            "expected_language": "Should detect as Spanish (has 'hola')"
        },
        {
            "name": "Performance Test: Quick response",
            "payload": {
                "message": "I need help",
                "thread_id": "test_perf_1",
                "phone": "+1234567892"
            },
            "measure_time": True
        },
        {
            "name": "Complete Flow Test",
            "payload": {
                "message": "I want to book an appointment",
                "thread_id": "test_flow_1",
                "phone": "+1234567893",
                "conversationId": "conv_123"
            },
            "description": "Tests full workflow execution with ainvoke"
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "x-webhook-secret": webhook_secret
    }
    
    results = []
    
    for test in test_cases:
        print(f"📋 Test: {test['name']}")
        print(f"   Payload: {test['payload']['message']}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                webhook_url,
                json=test['payload'],
                headers=headers,
                timeout=30
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                response_msg = result_data.get('message', '')
                
                # Check language detection
                is_spanish = any(spanish in response_msg.lower() for spanish in ['hola', 'maría', 'negocio'])
                
                print(f"   ✅ Status: {response.status_code}")
                print(f"   Response: {response_msg[:100]}...")
                
                if test.get('expected_language'):
                    print(f"   Language: {'Spanish' if is_spanish else 'English'} - {test['expected_language']}")
                
                if test.get('measure_time'):
                    print(f"   ⏱️  Response Time: {elapsed:.2f}s")
                
                results.append({
                    "test": test['name'],
                    "status": "PASS",
                    "time": elapsed,
                    "is_spanish": is_spanish
                })
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   Error: {response.text}")
                results.append({
                    "test": test['name'],
                    "status": "FAIL",
                    "error": response.text
                })
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({
                "test": test['name'],
                "status": "ERROR",
                "error": str(e)
            })
        
        print()
    
    # Summary
    print("\n📊 Test Summary:")
    passed = sum(1 for r in results if r['status'] == 'PASS')
    print(f"   Passed: {passed}/{len(results)}")
    
    # Performance analysis
    avg_time = sum(r.get('time', 0) for r in results if r['status'] == 'PASS') / max(passed, 1)
    print(f"   Average Response Time: {avg_time:.2f}s")
    
    # Language detection results
    spanish_tests = [r for r in results if 'is_spanish' in r]
    if spanish_tests:
        print(f"\n🌐 Language Detection Results:")
        for r in spanish_tests:
            print(f"   {r['test']}: {'Spanish' if r.get('is_spanish') else 'English'}")
    
    return passed == len(results)

if __name__ == "__main__":
    # First check if server is running
    try:
        health = requests.get("http://localhost:8123/health").json()
        print(f"✅ Server is running: {health}\n")
        
        if test_webhook_fixes():
            print("\n✅ All tests passed! Fixes are working correctly.")
        else:
            print("\n❌ Some tests failed.")
    except Exception as e:
        print(f"❌ Server not running: {e}")
        print("Please start the server with: python -m booking_agent.webapp")