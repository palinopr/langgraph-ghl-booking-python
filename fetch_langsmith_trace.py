#!/usr/bin/env python3
"""
Fetch LangSmith trace to see what's happening in production.
"""
import os
from dotenv import load_dotenv
from langsmith import Client
import json
from datetime import datetime

# Load environment
load_dotenv()

# Trace ID to fetch
TRACE_ID = "fed9b8c8-594c-4306-ad39-52edaa5b749a"


def fetch_trace(trace_id: str):
    """Fetch and analyze a LangSmith trace."""
    # Initialize LangSmith client
    client = Client(
        api_key=os.getenv("LANGSMITH_API_KEY"),
    )
    
    try:
        # Fetch the run (trace)
        print(f"Fetching trace: {trace_id}")
        print("=" * 60)
        
        run = client.read_run(trace_id)
        
        # Extract key information
        print(f"\n📊 TRACE SUMMARY")
        print(f"Name: {run.name}")
        print(f"Status: {run.status}")
        print(f"Start Time: {run.start_time}")
        print(f"End Time: {run.end_time}")
        print(f"Total Tokens: {run.token_count if hasattr(run, 'token_count') else 'N/A'}")
        
        # Show inputs
        print(f"\n📥 INPUTS:")
        if run.inputs:
            print(json.dumps(run.inputs, indent=2))
        else:
            print("No inputs recorded")
        
        # Show outputs
        print(f"\n📤 OUTPUTS:")
        if run.outputs:
            print(json.dumps(run.outputs, indent=2))
        else:
            print("No outputs recorded")
        
        # Show any errors
        if run.error:
            print(f"\n❌ ERROR:")
            print(run.error)
        
        # Get child runs (execution steps)
        print(f"\n🔄 EXECUTION FLOW:")
        # Try different approaches to get child runs
        try:
            child_runs = list(client.list_runs(
                parent_run_id=trace_id,
                limit=50
            ))
        except:
            # Fallback approach
            child_runs = []
            print("Note: Could not fetch child runs with parent_run_id filter")
        
        for i, child in enumerate(child_runs):
            print(f"\n{i+1}. {child.name}")
            print(f"   Type: {child.run_type}")
            print(f"   Status: {child.status}")
            if child.error:
                print(f"   Error: {child.error}")
            
            # Show specific details for certain run types
            if child.name == "process_message":
                print("   📝 Message Processing:")
                if child.inputs:
                    print(f"   Input: {json.dumps(child.inputs, indent=6)}")
                if child.outputs:
                    print(f"   Output: {json.dumps(child.outputs, indent=6)}")
            
            elif child.name == "handle_webhook_message":
                print("   🌐 Webhook Handler:")
                if child.inputs and 'data' in child.inputs:
                    data = child.inputs['data']
                    print(f"   Phone: {data.get('phone', 'N/A')}")
                    print(f"   Message: {data.get('message', 'N/A')}")
                
            elif child.name == "send_message":
                print("   📨 Message Sending:")
                if child.inputs:
                    print(f"   To: {child.inputs.get('contact_id', 'N/A')}")
                    print(f"   Message: {child.inputs.get('message', 'N/A')}")
                    print(f"   Type: {child.inputs.get('message_type', 'N/A')}")
        
        # Analysis
        print("\n" + "=" * 60)
        print("📊 ANALYSIS:")
        
        # Check if AI was used
        ai_used = any("ai" in child.name.lower() or "gpt" in child.name.lower() 
                      for child in child_runs)
        
        # Check if template was used
        template_used = any("template" in str(child.outputs).lower() 
                           for child in child_runs if child.outputs)
        
        print(f"✓ AI Engine Used: {'YES' if ai_used else 'NO'}")
        print(f"✓ Template Response: {'YES' if template_used else 'NO'}")
        print(f"✓ Total Steps: {len(child_runs)}")
        print(f"✓ Any Errors: {'YES' if run.error else 'NO'}")
        
        return run
        
    except Exception as e:
        print(f"❌ Error fetching trace: {str(e)}")
        print("\nPossible reasons:")
        print("1. Invalid trace ID")
        print("2. LangSmith API key not set")
        print("3. Trace not found in your project")
        return None


if __name__ == "__main__":
    print("🔍 LangSmith Trace Analysis")
    print("=" * 60)
    fetch_trace(TRACE_ID)