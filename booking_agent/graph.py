"""Main LangGraph workflow for the booking agent."""
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langsmith import traceable

from booking_agent.utils.state import BookingState
from booking_agent.utils.nodes import triage_node, collect_node, validate_node, booking_node


def route_from_triage(state: BookingState) -> Literal["collect", "END"]:
    """Route from triage node based on spam detection."""
    if state.get("is_spam", False):
        return END
    return "collect"


def route_from_collect(state: BookingState) -> Literal["collect", "validate", "END"]:
    """Route from collect node based on current step."""
    if state.get("current_step") == "validate":
        return "validate"
    
    # Check if we're waiting for user input (last message is from AI)
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], 'type') and messages[-1].type == "assistant":
        return END  # Wait for user response
    
    return "collect"  # Keep collecting


def route_from_validate(state: BookingState) -> Literal["collect", "book"]:
    """Route from validate node based on validation errors."""
    if state.get("validation_errors"):
        return "collect"  # Back to collect to fix errors
    return "book"


def route_from_booking(state: BookingState) -> Literal["END"]:
    """Always end after booking attempt."""
    return END


@traceable(name="create_booking_workflow", run_type="chain")
def create_booking_workflow():
    """Create and compile the booking workflow graph.
    
    Returns:
        Compiled LangGraph workflow
    """
    # Initialize the graph with our state
    workflow = StateGraph(BookingState)
    
    # Add all nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("collect", collect_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("book", booking_node)
    
    # Define the workflow edges
    # Start with triage
    workflow.add_edge(START, "triage")
    
    # From triage, either end (if spam) or go to collect
    workflow.add_conditional_edges(
        "triage",
        route_from_triage,
        {
            "collect": "collect",
            END: END
        }
    )
    
    # From collect, either keep collecting, go to validate, or end to wait for user
    workflow.add_conditional_edges(
        "collect",
        route_from_collect,
        {
            "collect": "collect",
            "validate": "validate",
            END: END
        }
    )
    
    # From validate, either back to collect (errors) or to book
    workflow.add_conditional_edges(
        "validate",
        route_from_validate,
        {
            "collect": "collect",
            "book": "book"
        }
    )
    
    # From book, always end
    workflow.add_conditional_edges(
        "book",
        route_from_booking,
        {
            END: END
        }
    )
    
    # Compile the graph
    return workflow.compile()


# Create the default workflow instance
booking_graph = create_booking_workflow()