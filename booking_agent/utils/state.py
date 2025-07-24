"""State definition for the booking workflow."""
from typing import TypedDict, List, Optional
from langchain_core.messages import BaseMessage


class BookingState(TypedDict):
    """State for the booking workflow.
    
    This state is passed between nodes in the LangGraph workflow
    and contains all information needed for the booking process.
    """
    messages: List[BaseMessage]
    customer_name: Optional[str]
    customer_goal: Optional[str]
    customer_budget: Optional[float]
    current_step: str  # "triage" | "collect" | "validate" | "book" | "complete"
    is_spam: bool
    validation_errors: List[str]
    booking_result: Optional[dict]
    thread_id: str