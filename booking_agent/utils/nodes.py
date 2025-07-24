"""Workflow nodes for the booking agent."""
import re
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langsmith import traceable
import yaml
import os

from booking_agent.utils.state import BookingState
from booking_agent.utils.tools import book_appointment, GHLClient


# Load business configuration
def load_config() -> Dict[str, Any]:
    """Load business configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), "../../config/config.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    # Default config if file doesn't exist
    return {
        "business": {
            "name": "FitLife Coaching",
            "minimum_budget": 1000,
            "timezone": "PST"
        }
    }


@traceable(name="triage_node", run_type="chain")
async def triage_node(state: BookingState) -> Dict[str, Any]:
    """Triage incoming messages to filter spam and determine if booking intent exists.
    
    This node:
    1. Checks for spam keywords
    2. Determines if the message shows booking intent
    3. Routes to collect or marks as spam
    """
    messages = state.get("messages", [])
    if not messages:
        return {
            "is_spam": True,
            "current_step": "complete",
            "messages": []
        }
    
    last_message = messages[-1].content.lower()
    
    # Spam detection
    spam_keywords = ["crypto", "investment", "viagra", "casino", "lottery", "prize"]
    if any(keyword in last_message for keyword in spam_keywords):
        return {
            "is_spam": True,
            "current_step": "complete",
            "messages": messages + [AIMessage(content="Sorry, I can only help with fitness coaching appointments.")]
        }
    
    # Check for booking intent
    booking_keywords = ["appointment", "book", "schedule", "meet", "consultation", "fitness", "training", "coach"]
    has_booking_intent = any(keyword in last_message for keyword in booking_keywords)
    
    if has_booking_intent or len(messages) == 1:  # First message gets benefit of doubt
        return {
            "messages": messages,
            "is_spam": False,
            "current_step": "collect"
        }
    else:
        return {
            "is_spam": True,
            "current_step": "complete",
            "messages": messages + [AIMessage(content="I'm here to help you book a fitness consultation. Would you like to schedule an appointment?")]
        }


@traceable(name="collect_node", run_type="chain")
async def collect_node(state: BookingState) -> Dict[str, Any]:
    """Collect customer information through conversation.
    
    This node:
    1. Extracts customer name, goal, and budget from messages
    2. Asks follow-up questions for missing information
    3. Routes to validate when all info is collected
    """
    messages = state.get("messages", [])
    customer_name = state.get("customer_name")
    customer_goal = state.get("customer_goal")
    customer_budget = state.get("customer_budget")
    
    # Initialize LLM for extraction
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    
    # Extract information from conversation
    extraction_prompt = f"""Extract the following information from this conversation:
    - Customer name
    - Fitness goal (e.g., weight loss, muscle gain, general fitness)
    - Budget (monthly amount in dollars)
    
    Current values:
    - Name: {customer_name or 'Not provided'}
    - Goal: {customer_goal or 'Not provided'}
    - Budget: {customer_budget or 'Not provided'}
    
    Conversation:
    {[msg.content for msg in messages]}
    
    Return ONLY a JSON object with keys: name, goal, budget (as number or null)
    """
    
    response = await llm.ainvoke(extraction_prompt)
    
    # Parse extraction (simple parsing - in production use proper JSON parsing)
    try:
        import json
        extracted = json.loads(response.content)
        
        # Update state with extracted values
        if extracted.get("name") and not customer_name:
            customer_name = extracted["name"]
        if extracted.get("goal") and not customer_goal:
            customer_goal = extracted["goal"]
        if extracted.get("budget") and not customer_budget:
            customer_budget = float(extracted["budget"])
    except:
        pass  # Continue with conversation if parsing fails
    
    # Check what's missing and ask for it
    missing_info = []
    if not customer_name:
        missing_info.append("your name")
    if not customer_goal:
        missing_info.append("your fitness goal")
    if not customer_budget:
        missing_info.append("your monthly budget")
    
    if missing_info:
        # Ask for missing information
        question = f"Thanks for your interest! To book your consultation, I'll need {', '.join(missing_info)}. Could you please provide that?"
        return {
            "messages": messages + [AIMessage(content=question)],
            "customer_name": customer_name,
            "customer_goal": customer_goal,
            "customer_budget": customer_budget,
            "current_step": "collect"
        }
    else:
        # All info collected, move to validation
        return {
            "messages": messages,
            "customer_name": customer_name,
            "customer_goal": customer_goal,
            "customer_budget": customer_budget,
            "current_step": "validate"
        }


@traceable(name="validate_node", run_type="chain")
async def validate_node(state: BookingState) -> Dict[str, Any]:
    """Validate collected information against business rules.
    
    This node:
    1. Checks if budget meets minimum requirement
    2. Validates all required fields are present
    3. Routes to booking or back to collect with errors
    """
    config = load_config()
    minimum_budget = config["business"]["minimum_budget"]
    
    customer_name = state.get("customer_name")
    customer_goal = state.get("customer_goal")
    customer_budget = state.get("customer_budget", 0)
    messages = state.get("messages", [])
    
    validation_errors = []
    
    # Validate required fields
    if not customer_name:
        validation_errors.append("Name is required")
    if not customer_goal:
        validation_errors.append("Fitness goal is required")
    if not customer_budget:
        validation_errors.append("Budget is required")
    
    # Validate budget minimum
    if customer_budget and customer_budget < minimum_budget:
        validation_errors.append(f"Our programs start at ${minimum_budget}/month")
    
    if validation_errors:
        # Send validation errors and go back to collect
        error_message = f"I notice a few things: {', '.join(validation_errors)}. Could you help me with this information?"
        return {
            "messages": messages + [AIMessage(content=error_message)],
            "validation_errors": validation_errors,
            "current_step": "collect"
        }
    else:
        # Validation passed, proceed to booking
        return {
            "messages": messages,
            "validation_errors": [],
            "current_step": "book"
        }


@traceable(name="booking_node", run_type="chain")
async def booking_node(state: BookingState) -> Dict[str, Any]:
    """Book the appointment in GoHighLevel.
    
    This node:
    1. Creates/updates contact in GHL
    2. Finds available appointment slot
    3. Books the appointment
    4. Returns confirmation message
    """
    customer_name = state["customer_name"]
    customer_goal = state["customer_goal"]
    customer_budget = state["customer_budget"]
    messages = state.get("messages", [])
    
    # Extract phone number from thread_id or use placeholder
    phone = state.get("thread_id", "whatsapp_user")
    
    try:
        # Book the appointment using our GHL tools
        result = await book_appointment(
            customer_name=customer_name,
            customer_phone=phone,
            customer_goal=customer_goal,
            customer_budget=customer_budget
        )
        
        if result["success"]:
            confirmation_message = result["message"]
            return {
                "messages": messages + [AIMessage(content=confirmation_message)],
                "booking_result": result,
                "current_step": "complete"
            }
        else:
            error_message = f"I'm having trouble booking your appointment: {result.get('error', 'Unknown error')}. Let me try again or connect you with our team."
            return {
                "messages": messages + [AIMessage(content=error_message)],
                "booking_result": result,
                "current_step": "complete"
            }
    except Exception as e:
        # Handle any booking errors
        error_message = "I encountered an issue while booking your appointment. Our team will reach out to you directly to complete the booking."
        return {
            "messages": messages + [AIMessage(content=error_message)],
            "booking_result": {"success": False, "error": str(e)},
            "current_step": "complete"
        }