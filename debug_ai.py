#!/usr/bin/env python3
"""Debug AI responses."""
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

async def debug_ai():
    """Debug raw AI responses."""
    llm = ChatOpenAI(
        model="gpt-4-1106-preview",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt = """You are an AI assistant for AI Outlet Media, specializing in AI automation solutions.

Customer asks: "Do you do automation?"

Respond ONLY with a valid JSON object (no markdown, no extra text):
{"response": "Your 2-3 sentence message", "notes": "Notes", "insights": "Insights", "pain_points": [], "interests": [], "qualification_score": 0, "objections": [], "next_action": "gather_requirements", "missing_info": []}"""
    
    print("Testing AI response...")
    response = await llm.ainvoke(prompt)
    print(f"Raw response: {response.content}")
    print(f"Type: {type(response.content)}")

if __name__ == "__main__":
    asyncio.run(debug_ai())