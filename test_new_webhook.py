#!/usr/bin/env python3
"""Test script for the new LangGraph webapp webhook endpoint."""

import requests
import json
import os
from datetime import datetime

def test_webhook():
    """Test the new webhook endpoint with various scenarios."""
    
    # Get webhook URL and secret from environment or use defaults
    webhook_url = os.getenv("WEBHOOK_URL", "http://localhost:8123/webhook")
    webhook_secret = os.getenv("GHL_WEBHOOK_SECRET", "test-secret")
    
    print(f"🧪 Testing webhook at: {webhook_url}")
    print(f"⏰ Time: {datetime.now().strftime('%I:%M %p')}\n")
    
    # Test scenarios
    test_cases = [
        {
            "name": "Basic greeting",
            "payload": {
                "message": "Hi I need help growing my business",
                "thread_id": "test_thread_1",
                "phone": "+1234567890"
            }
        },
        {
            "name": "Spanish greeting",
            "payload": {
                "message": "Hola necesito ayuda con mi negocio",
                "thread_id": "test_thread_2",
                "phone": "+1234567891"
            }
        },
        {
            "name": "Different message field",
            "payload": {
                "text": "I want to book an appointment",
                "phone": "+1234567892"
            }
        }
    ]
    
    # Run tests
    results = []
    for test in test_cases:
        print(f"📋 Test: {test['name']}")
        print(f"   Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            # Make request with webhook secret header
            headers = {
                "Content-Type": "application/json",
                "x-webhook-secret": webhook_secret
            }
            
            response = requests.post(
                webhook_url,
                json=test['payload'],
                headers=headers,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {result.get('message', 'No message')}")
                print(f"   ✅ SUCCESS\n")
                results.append({"test": test['name'], "status": "PASS"})
            else:
                print(f"   ❌ FAILED: {response.text}\n")
                results.append({"test": test['name'], "status": "FAIL", "error": response.text})
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}\n")
            results.append({"test": test['name'], "status": "ERROR", "error": str(e)})
    
    # Summary
    print("\n📊 Test Summary:")
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    for result in results:
        status_icon = "✅" if result['status'] == 'PASS' else "❌"
        print(f"   {status_icon} {result['test']} - {result['status']}")
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    return passed == total

if __name__ == "__main__":
    # First test locally
    print("🚀 Testing New LangGraph Webhook Implementation\n")
    
    # Test health endpoint first
    health_url = os.getenv("WEBHOOK_URL", "http://localhost:8123").rstrip('/') + "/health"
    try:
        health_response = requests.get(health_url, timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"🏥 Health Check: {health_data}")
            print(f"   Workflow Loaded: {health_data.get('workflow_loaded', False)}\n")
    except:
        print("⚠️  Health check failed - service might not be running\n")
    
    # Run webhook tests
    success = test_webhook()
    
    if success:
        print("\n✅ All tests passed! Webhook is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the webhook implementation.")