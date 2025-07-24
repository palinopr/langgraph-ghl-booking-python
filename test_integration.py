#!/usr/bin/env python3
"""
Integration test to verify webhook and workflow integration.
Run this script to test the connection between David's API and Sofia's workflow.
"""
import asyncio
import json
from datetime import datetime

# Test direct workflow invocation
async def test_workflow_direct():
    """Test Sofia's workflow directly."""
    print("\n=== Testing Sofia's Workflow Directly ===")
    try:
        from booking_agent.graph import create_booking_workflow
        from langchain_core.messages import HumanMessage
        
        workflow = create_booking_workflow()
        
        # Test state
        test_state = {
            "messages": [HumanMessage(content="Hi, I need help with Facebook ads")],
            "thread_id": "test-thread-123",
            "customer_name": None,
            "customer_goal": None,
            "customer_budget": None,
            "current_step": "triage",
            "is_spam": False,
            "validation_errors": [],
            "booking_result": None
        }
        
        config = {"configurable": {"thread_id": "test-thread-123"}}
        result = await workflow.ainvoke(test_state, config)
        
        print(f"✅ Workflow executed successfully")
        print(f"   - Current step: {result.get('current_step')}")
        print(f"   - Is spam: {result.get('is_spam')}")
        print(f"   - Messages count: {len(result.get('messages', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# Test webhook integration
async def test_webhook_integration():
    """Test David's webhook with workflow integration."""
    print("\n=== Testing Webhook-Workflow Integration ===")
    try:
        # Import webhook components
        from api.webhook import process_through_workflow
        from api.models import WebhookRequest
        from booking_agent.graph import create_booking_workflow
        
        workflow = create_booking_workflow()
        
        # Create a test webhook request
        webhook_request = WebhookRequest(
            thread_id="webhook-test-456",
            phone="+1234567890",
            message="I want to learn about Facebook advertising. My budget is $2000.",
            signature="test-signature",
            timestamp=datetime.utcnow()
        )
        
        # Process through workflow
        result = await process_through_workflow(workflow, webhook_request)
        
        print(f"✅ Webhook integration successful")
        print(f"   - Response: {result.get('response')[:100]}...")
        print(f"   - Is spam: {result.get('is_spam')}")
        print(f"   - Validation errors: {result.get('validation_errors')}")
        print(f"   - Booking result: {result.get('booking_result')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# Test full API server
async def test_api_server():
    """Test the full API server integration."""
    print("\n=== Testing Full API Server ===")
    try:
        # Check if aiohttp is available for HTTP testing
        try:
            import aiohttp
        except ImportError:
            print("⚠️  Skipping API server test (aiohttp not installed)")
            print("   Run: pip install aiohttp")
            return None
        
        # Try to connect to the API
        async with aiohttp.ClientSession() as session:
            try:
                # Test health endpoint
                async with session.get('http://localhost:3000/health') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✅ API server is running")
                        print(f"   - Status: {data.get('status')}")
                        print(f"   - Version: {data.get('version')}")
                        return True
                    else:
                        print(f"⚠️  API server returned status {resp.status}")
                        return False
                        
            except aiohttp.ClientConnectorError:
                print("⚠️  API server is not running on localhost:3000")
                print("   Start it with: python -m api.webhook")
                return False
                
    except Exception as e:
        print(f"❌ API server test failed: {str(e)}")
        return False


async def main():
    """Run all integration tests."""
    print("🔧 WhatsApp Booking System - Integration Test")
    print("=" * 50)
    
    results = {
        "workflow": await test_workflow_direct(),
        "webhook": await test_webhook_integration(),
        "api": await test_api_server()
    }
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    for test, result in results.items():
        if result is None:
            status = "⚠️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"   {test.capitalize()}: {status}")
    
    # Overall result
    failures = [r for r in results.values() if r is False]
    if not failures:
        print("\n✅ All tests passed! Integration is working correctly.")
    else:
        print(f"\n❌ {len(failures)} test(s) failed. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())