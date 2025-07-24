#!/usr/bin/env python3
"""Test direct LangGraph API call with streaming."""

import os
import json
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

LANGGRAPH_URL = "https://ghl-python-booking-c30b52e8c48d5005b60fdf394ffbe3aa.us.langgraph.app"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")


async def test_langgraph_stream():
    """Test the LangGraph streaming API directly."""
    
    langgraph_input = {
        "input": {
            "messages": [
                {
                    "type": "human",
                    "content": "Hi, I want to book a fitness consultation. My name is Rachel Test, budget is $2500/month, and I want to lose weight."
                }
            ],
            "thread_id": "test_direct_001",
            "customer_name": "Rachel Test",
            "customer_phone": "+1234567890"
        },
        "config": {
            "configurable": {
                "thread_id": "test_direct_001"
            }
        },
        "assistant_id": "agent",
        "stream_mode": "values"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": LANGSMITH_API_KEY
    }
    
    print(f"Testing LangGraph API at: {LANGGRAPH_URL}/runs/stream")
    print(f"API Key (first 10 chars): {LANGSMITH_API_KEY[:10]}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{LANGGRAPH_URL}/runs/stream",
                json=langgraph_input,
                headers=headers,
                timeout=30.0
            )
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("\nStreaming response:")
                print("-" * 50)
                
                chunk_count = 0
                async for line in response.aiter_lines():
                    if line.strip():
                        chunk_count += 1
                        print(f"\nChunk {chunk_count}:")
                        try:
                            data = json.loads(line)
                            print(json.dumps(data, indent=2))
                        except json.JSONDecodeError:
                            print(f"Raw line: {line}")
                
                print(f"\nTotal chunks received: {chunk_count}")
            else:
                print(f"\nError response: {response.text}")
                
        except Exception as e:
            print(f"\nError: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_langgraph_stream())