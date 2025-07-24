"""Minimal graph wrapper for LangGraph deployment."""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Any
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MinimalState(TypedDict):
    """Minimal state for the graph."""
    phone: str
    message: str
    response: str

async def process_webhook(state: MinimalState) -> MinimalState:
    """Process webhook using stateless handler."""
    from stateless_booking.webhook_handler import handle_webhook_message
    
    result = await handle_webhook_message({
        "phone": state.get("phone", ""),
        "message": state.get("message", "")
    })
    
    state["response"] = result.get("message", "")
    return state

# Create the graph
workflow = StateGraph(MinimalState)
workflow.add_node("process", process_webhook)
workflow.add_edge("process", END)
workflow.set_entry_point("process")

# Compile to get the graph
booking_graph = workflow.compile()