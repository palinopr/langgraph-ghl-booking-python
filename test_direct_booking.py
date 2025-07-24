#!/usr/bin/env python3
"""Test direct booking flow without webhook."""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from booking_agent.graph import create_booking_workflow
from langchain_core.messages import HumanMessage

# Load environment
load_dotenv()

async def test_direct_booking():
    """Test the booking flow directly."""
    print("=== DIRECT BOOKING FLOW TEST ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create workflow
    workflow = create_booking_workflow()
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content="Hola, necesito ayuda con marketing")],
        "thread_id": f"test_direct_{int(datetime.now().timestamp())}",
        "customer_phone": "+1234567890"
    }
    
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}
    
    print("\n🚀 Starting booking flow...")
    print(f"Thread ID: {initial_state['thread_id']}")
    
    # Run the workflow
    try:
        # Process each message
        messages = [
            "Hola, necesito ayuda con marketing",
            "Soy Carlos Mendez", 
            "Quiero aumentar las ventas de mi restaurante",
            "La gente no conoce mi restaurante nuevo",
            "Puedo invertir $800 al mes",
            "carlos@mirestaurante.com",
            "El martes está bien",
            "10 AM sería perfecto"
        ]
        
        for i, msg in enumerate(messages):
            print(f"\n📱 USER: {msg}")
            
            # Update state with new message
            if i > 0:  # Skip first message as it's already in initial state
                initial_state["messages"].append(HumanMessage(content=msg))
            
            # Run workflow
            result = await workflow.ainvoke(initial_state, config)
            
            # Get last AI message
            ai_messages = [m for m in result.get("messages", []) if hasattr(m, 'type') and m.type == "ai"]
            if ai_messages:
                last_response = ai_messages[-1].content
                print(f"🤖 BOT: {last_response}")
            
            # Check if booking completed
            if result.get("booking_result", {}).get("success"):
                print("\n✅ BOOKING SUCCESSFUL!")
                print(f"   Contact ID: {result['booking_result'].get('contact_id')}")
                print(f"   Appointment ID: {result['booking_result'].get('appointment_id')}")
                print(f"   Message: {result['booking_result'].get('message')}")
                break
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Testing direct booking flow...")
    print(f"OpenAI API Key: {os.getenv('OPENAI_API_KEY')[:20]}...")
    print(f"GHL API Key: {os.getenv('GHL_API_KEY')[:10]}...")
    
    asyncio.run(test_direct_booking())