"""Minimal graph wrapper for LangGraph deployment."""
from langchain_core.runnables import RunnableLambda
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stateless_booking.webhook_handler import handle_webhook_message

# Create a minimal graph that just calls the stateless handler
booking_graph = RunnableLambda(
    lambda x: handle_webhook_message({
        "phone": x.get("phone", ""),
        "message": x.get("message", "")
    })
)