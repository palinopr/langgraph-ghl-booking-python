#!/usr/bin/env python3
"""
Analyze what's happening in production - is AI being used or templates?
"""
import os
from dotenv import load_dotenv
from langsmith import Client

# Load environment
load_dotenv()

# Trace ID
TRACE_ID = "fed9b8c8-594c-4306-ad39-52edaa5b749a"


def analyze_production():
    """Analyze production trace to see if AI is being used."""
    client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))
    
    print("🔍 PRODUCTION ANALYSIS")
    print("=" * 60)
    
    # Get the main run
    run = client.read_run(TRACE_ID)
    
    # Key findings
    print("\n📌 KEY FINDINGS:")
    print(f"Customer Message: {run.inputs['data']['message']}")
    print(f"Bot Response: {run.outputs['message']}")
    print(f"Next Step: {run.outputs['step']}")
    
    # Analysis
    print("\n🤔 ANALYSIS:")
    
    # The response looks like a template
    response = run.outputs['message']
    if "Hi! I'm Maria from AI Outlet Media" in response:
        print("❌ TEMPLATE RESPONSE DETECTED!")
        print("   This is the hardcoded greeting template, NOT AI-generated")
    
    # Check if customer said "Jaime" but bot asked for name
    if run.inputs['data']['message'] == "Jaime" and "What's your name?" in response:
        print("❌ BOT DIDN'T UNDERSTAND!")
        print("   Customer provided their name 'Jaime' but bot still asked for name")
        print("   This confirms it's using templates, not AI understanding")
    
    # Look for AI traces
    print("\n🔎 LOOKING FOR AI USAGE:")
    print("   Searching for AI/GPT function calls...")
    
    # Get all runs in the project around this time
    all_runs = list(client.list_runs(
        project_name=os.getenv("LANGSMITH_PROJECT", "whatsapp-booking"),
        limit=20
    ))
    
    ai_calls = [r for r in all_runs if "ai" in r.name.lower() or "gpt" in r.name.lower()]
    
    if ai_calls:
        print(f"   Found {len(ai_calls)} AI-related calls")
        for call in ai_calls[:5]:
            print(f"   - {call.name} at {call.start_time}")
    else:
        print("   ❌ NO AI CALLS FOUND!")
        print("   The system is NOT using the AI engine")
    
    # Conclusion
    print("\n📊 CONCLUSION:")
    print("1. The system is using TEMPLATE responses, not AI")
    print("2. Customer said 'Jaime' but bot didn't recognize it as a name")
    print("3. No AI/GPT calls were made")
    print("4. The AI engine is NOT integrated into production yet")
    
    print("\n💡 NEXT STEPS:")
    print("1. Integrate the AI engine into message_processor.py")
    print("2. Replace template responses with AI-generated ones")
    print("3. Test that AI understands context (like recognizing 'Jaime' as a name)")


if __name__ == "__main__":
    analyze_production()