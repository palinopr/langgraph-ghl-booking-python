"""
Message processor - handles step-by-step conversation logic.
Each step processes ONE message and returns ONE response.
"""
import re
from typing import Dict, Any
from .response_templates import get_template


class MessageProcessor:
    """Process messages based on current conversation step."""
    
    def process_message(self, message: str, step: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single message based on current step.
        
        Returns:
            Dict with next_step, updates, and response
        """
        # Route to appropriate step handler
        if step == "greeting":
            return self._process_greeting(message, language)
        elif step == "name":
            return self._process_name(message, language)
        elif step == "goal":
            return self._process_goal(message, language, state)
        elif step == "pain":
            return self._process_pain(message, language, state)
        elif step == "budget":
            return self._process_budget(message, language, state)
        elif step == "email":
            return self._process_email(message, language, state)
        elif step == "day":
            return self._process_day(message, language, state)
        elif step == "time":
            return self._process_time(message, language, state)
        else:
            # Terminal states or unknown
            return {
                "next_step": step,
                "updates": {},
                "response": get_template("conversation_complete", language)
            }
    
    def _process_greeting(self, message: str, language: str) -> Dict[str, Any]:
        """Process first message - detect language and greet."""
        # Detect language
        spanish_indicators = ["hola", "buenos", "necesito", "ayuda", "quiero"]
        detected_lang = "es" if any(word in message.lower() for word in spanish_indicators) else "en"
        
        return {
            "next_step": "name",
            "updates": {"language": detected_lang},
            "response": get_template("greeting", detected_lang)
        }
    
    def _process_name(self, message: str, language: str) -> Dict[str, Any]:
        """Extract name from message."""
        # Simple name extraction (in production, use NER or LLM)
        name = message.strip()
        if len(name.split()) <= 4 and len(name) > 1:  # Reasonable name
            return {
                "next_step": "goal",
                "updates": {"customer_name": name},
                "response": get_template("ask_goal", language, name=name)
            }
        else:
            return {
                "next_step": "name",
                "updates": {},
                "response": get_template("ask_name_again", language)
            }
    
    def _process_goal(self, message: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract business goal."""
        goal = message.strip()[:200]  # Limit length
        if len(goal) > 5:
            return {
                "next_step": "pain",
                "updates": {"customer_goal": goal},
                "response": get_template("ask_pain", language)
            }
        else:
            return {
                "next_step": "goal",
                "updates": {},
                "response": get_template("ask_goal_again", language)
            }
    
    def _process_pain(self, message: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pain point."""
        pain = message.strip()[:200]
        if len(pain) > 5:
            return {
                "next_step": "budget",
                "updates": {"customer_pain_point": pain},
                "response": get_template("ask_budget", language)
            }
        else:
            return {
                "next_step": "pain",
                "updates": {},
                "response": get_template("ask_pain_again", language)
            }
    
    def _process_budget(self, message: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate budget."""
        # Extract number from message
        numbers = re.findall(r'\d+', message)
        budget = int(numbers[0]) if numbers else 0
        
        if budget >= 300:
            return {
                "next_step": "email",
                "updates": {"customer_budget": budget},
                "response": get_template("ask_email", language)
            }
        elif budget > 0:
            # Budget too low
            return {
                "next_step": "complete",
                "updates": {"customer_budget": budget},
                "response": get_template("budget_too_low", language)
            }
        else:
            # Couldn't extract budget
            return {
                "next_step": "budget",
                "updates": {},
                "response": get_template("ask_budget_again", language)
            }
    
    def _process_email(self, message: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate email."""
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_regex, message)
        
        if emails:
            return {
                "next_step": "day",
                "updates": {"customer_email": emails[0]},
                "response": get_template("ask_day", language)
            }
        else:
            return {
                "next_step": "email",
                "updates": {},
                "response": get_template("ask_email_again", language)
            }
    
    def _process_day(self, message: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract preferred day."""
        day_map = {
            "en": ["tuesday", "wednesday", "thursday", "friday"],
            "es": ["martes", "miércoles", "jueves", "viernes"]
        }
        
        message_lower = message.lower()
        for day in day_map.get(language, day_map["en"]):
            if day in message_lower:
                # In production, fetch real slots from GHL calendar
                times = ["10:00 AM", "2:00 PM", "4:00 PM"]
                return {
                    "next_step": "time",
                    "updates": {"preferred_day": day.capitalize()},
                    "response": get_template("ask_time", language, day=day.capitalize(), times=", ".join(times))
                }
        
        return {
            "next_step": "day",
            "updates": {},
            "response": get_template("ask_day_again", language)
        }
    
    def _process_time(self, message: str, language: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract time and book appointment."""
        # Simple time extraction
        time_patterns = [r'\d{1,2}:\d{2}', r'\d{1,2}\s*[ap]m', r'\d{1,2}\s*AM|PM']
        
        for pattern in time_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                time = matches[0]
                # In production, actually book via GHL API
                return {
                    "next_step": "scheduled",
                    "updates": {
                        "preferred_time": time,
                        "appointment_id": "mock-appointment-123"
                    },
                    "response": get_template("appointment_confirmed", language, 
                                           day=state.get("preferred_day"),
                                           time=time,
                                           email=state.get("customer_email"))
                }
        
        return {
            "next_step": "time",
            "updates": {},
            "response": get_template("ask_time_again", language)
        }