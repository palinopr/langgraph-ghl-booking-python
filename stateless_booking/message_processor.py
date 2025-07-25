"""
Message processor - handles step-by-step conversation logic.
Each step processes ONE message and returns ONE response.
"""
import re
import asyncio
from typing import Dict, Any, List
from langsmith import traceable
from .response_templates import get_template
from .ai_engine import AIConversationEngine


class MessageProcessor:
    """Process messages based on current conversation step."""
    
    def __init__(self):
        """Initialize with AI engine."""
        self.ai_engine = AIConversationEngine()
    
    @traceable(name="process_message", run_type="chain")
    def process_message(self, message: str, step: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single message based on current step.
        
        Returns:
            Dict with next_step, updates, and response
        """
        # Use AI engine for ALL processing
        return asyncio.run(self._process_with_ai(message, step, language, state))
    
    async def _process_with_ai(self, message: str, step: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process message using AI engine."""
        # Build conversation history from state
        conversation_history = []
        
        # Add previous exchanges if available
        if state.get("customer_name"):
            conversation_history.append({"role": "ai", "content": "What's your name?"})
            conversation_history.append({"role": "customer", "content": state["customer_name"]})
        
        if state.get("customer_goal"):
            conversation_history.append({"role": "ai", "content": "What specific goals are you looking to achieve?"})
            conversation_history.append({"role": "customer", "content": state["customer_goal"]})
            
        if state.get("customer_pain_point"):
            conversation_history.append({"role": "ai", "content": "What's the biggest challenge you're facing?"})
            conversation_history.append({"role": "customer", "content": state["customer_pain_point"]})
            
        if state.get("customer_budget"):
            conversation_history.append({"role": "ai", "content": "What's your monthly marketing budget?"})
            conversation_history.append({"role": "customer", "content": str(state["customer_budget"])})
        
        # Get AI response
        ai_result = await self.ai_engine.process_message(
            message=message,
            conversation_history=conversation_history,
            customer_state=state
        )
        
        # Smart state extraction and next step logic
        updates = {}
        next_step = step
        
        # Process based on current step and AI insights
        if step in ["greeting", "name"]:
            # Extract name from short messages
            if len(message.split()) <= 3 and not any(char in message for char in "?@#$%^&*"):
                updates["customer_name"] = message.strip()
                next_step = "goal"
        
        elif step == "goal":
            # Goal provided
            if len(message) > 5:
                updates["customer_goal"] = message.strip()[:200]
                next_step = "pain"
        
        elif step == "pain":
            # Pain point provided
            if len(message) > 5:
                updates["customer_pain_point"] = message.strip()[:200]
                next_step = "budget"
        
        elif step == "budget":
            # Extract budget
            numbers = re.findall(r'\d+', message)
            if numbers:
                budget = int(numbers[0])
                updates["customer_budget"] = budget
                if budget >= 300:
                    next_step = "email"
                else:
                    next_step = "complete"  # Budget too low
        
        elif step == "email":
            # Extract email
            email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_regex, message)
            if emails:
                updates["customer_email"] = emails[0]
                next_step = "day"
        
        elif step == "day":
            # Extract day
            days = ["tuesday", "wednesday", "thursday", "friday", "martes", "miércoles", "jueves", "viernes"]
            message_lower = message.lower()
            for day in days:
                if day in message_lower:
                    updates["preferred_day"] = day.capitalize()
                    next_step = "time"
                    break
        
        elif step == "time":
            # Extract time
            time_patterns = [r'\d{1,2}:\d{2}', r'\d{1,2}\s*[ap]m', r'\d{1,2}\s*AM|PM']
            for pattern in time_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                if matches:
                    updates["preferred_time"] = matches[0]
                    updates["appointment_id"] = "ai-appointment-123"
                    next_step = "scheduled"
                    break
        
        return {
            "next_step": next_step,
            "updates": updates,
            "response": ai_result["response"]
        }