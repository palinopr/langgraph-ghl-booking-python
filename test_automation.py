#!/usr/bin/env python3
"""
Test AI automation response.
"""
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment
load_dotenv()

# AI Prompt
AUTOMATION_PROMPT = """You are an AI assistant for AI Outlet Media, specializing in AI automation solutions.

Keep responses SHORT (2-3 sentences). Be professional, not salesy.

Services: AI WhatsApp Automation, AI Customer Service Bots, AI Sales Automation, AI Workflow Automation, Custom AI Solutions.

Customer asks: "Do you do automation?"

Respond professionally in 2-3 sentences. Confirm you do automation and ask what business processes they want to automate."""


async def test_automation_response():
    """Test AI response to automation question."""
    # Initialize ChatGPT
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Get response
    response = await llm.ainvoke(AUTOMATION_PROMPT)
    
    print("Customer: Do you do automation?\n")
    print(f"AI: {response.content}")
    
    # Verify it's short (2-3 sentences)
    sentences = response.content.count('.') + response.content.count('?')
    print(f"\n✓ Response length: {sentences} sentences")
    
    return response.content


if __name__ == "__main__":
    asyncio.run(test_automation_response())