#!/usr/bin/env python3
"""
Test script for the FastAPI webhook server.
Run this to verify the API is working correctly.
"""
import asyncio
import httpx
import json
from datetime import datetime


BASE_URL = "http://localhost:3000"


async def test_health_endpoint():
    """Test the health check endpoint."""
    print("\n🔍 Testing /health endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            print("✅ Health check passed!")
        except Exception as e:
            print(f"❌ Health check failed: {e}")


async def test_metrics_endpoint():
    """Test the metrics endpoint."""
    print("\n📊 Testing /metrics endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/metrics")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            assert response.status_code == 200
            print("✅ Metrics endpoint passed!")
        except Exception as e:
            print(f"❌ Metrics endpoint failed: {e}")


async def test_webhook_endpoint():
    """Test the webhook endpoint."""
    print("\n📨 Testing /webhook endpoint...")
    
    test_data = {
        "message": "Hi, I want to book an appointment. My budget is $1500.",
        "phone": "+1234567890",
        "thread_id": f"test_thread_{datetime.utcnow().timestamp()}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/webhook",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                print("✅ Webhook endpoint passed!")
            else:
                print(f"⚠️ Webhook returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Webhook endpoint failed: {e}")


async def test_rate_limiting():
    """Test rate limiting (should limit to 30 requests per minute)."""
    print("\n⏱️ Testing rate limiting...")
    
    test_data = {
        "message": "Test message",
        "phone": "+1234567890",
        "thread_id": "rate_limit_test"
    }
    
    async with httpx.AsyncClient() as client:
        # Send 35 requests quickly
        results = []
        for i in range(35):
            try:
                response = await client.post(
                    f"{BASE_URL}/webhook",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                )
                results.append(response.status_code)
                
                if i % 10 == 0:
                    print(f"  Sent {i+1} requests...")
                    
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
        
        # Count successful vs rate limited
        successful = sum(1 for code in results if code == 200)
        rate_limited = sum(1 for code in results if code == 429)
        
        print(f"\n  Results: {successful} successful, {rate_limited} rate limited")
        
        if rate_limited > 0:
            print("✅ Rate limiting is working!")
        else:
            print("⚠️ Rate limiting might not be configured properly")


async def main():
    """Run all tests."""
    print("🚀 Starting API tests...")
    print(f"   Testing server at: {BASE_URL}")
    print("   Make sure the server is running with: python -m api.webhook")
    
    await test_health_endpoint()
    await test_metrics_endpoint()
    await test_webhook_endpoint()
    
    # Optional: Uncomment to test rate limiting
    # await test_rate_limiting()
    
    print("\n✨ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())