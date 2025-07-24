#!/usr/bin/env python3
"""Simple test to debug webhook endpoint."""

import requests
import json

def test_simple():
    """Test with a simple message."""
    url = "http://localhost:8123/webhook"
    headers = {
        "Content-Type": "application/json",
        "x-webhook-secret": "your_webhook_secret_here"
    }
    
    payload = {
        "message": "Hi",
        "thread_id": "test_simple",
        "phone": "+1234567890"
    }
    
    print(f"Testing: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_simple()