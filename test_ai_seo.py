#!/usr/bin/env python3
"""
Quick test of AI answering SEO question intelligently.
"""
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment
load_dotenv()

# AI System Prompt
QUICK_PROMPT = """You are an AI booking assistant for AI Outlet Media.

Services we offer:
- Local SEO ($300-500/month) - We help businesses rank #1 on Google Maps
- Google Ads Management ($300-1000/month)  
- Social Media Marketing ($300-800/month)
- Website Development ($2000-5000 one-time)
- AI Automation ($500-2000/month)

Customer asks: "Do you guys do SEO?"

Provide a natural, engaging response that:
1. Confirms we do SEO
2. Mentions it's one of our specialties
3. Asks a qualifying question about their business
4. Shows expertise without being pushy"""


async def test_seo_response():
    """Test AI response to SEO question."""
    # Initialize ChatGPT
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Get response
    response = await llm.ainvoke(QUICK_PROMPT)
    
    print("Customer: Do you guys do SEO?\n")
    print(f"AI: {response.content}")
    
    return response.content


if __name__ == "__main__":
    asyncio.run(test_seo_response())