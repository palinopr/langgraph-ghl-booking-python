"""
Mock implementations for testing.
"""
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, Mock
import re
import random
from datetime import datetime, timedelta


class MockTriageNode:
    """Mock implementation of triage node."""
    
    SPAM_KEYWORDS = [
        'free', 'click here', 'bit.ly', 'win now', 'congratulations',
        'viagra', 'casino', 'prize', 'urgent', 'act now'
    ]
    
    async def __call__(self, state: Dict) -> Dict:
        """Check if message is spam."""
        messages = state.get("messages", [])
        if not messages:
            return {**state, "messages": messages, "is_spam": False, "current_step": "collect"}
        
        last_message = messages[-1].content.lower()
        
        # Check for spam keywords
        is_spam = any(keyword in last_message for keyword in self.SPAM_KEYWORDS)
        
        # Check for suspicious URLs
        if re.search(r'bit\.ly|tinyurl|goo\.gl', last_message):
            is_spam = True
        
        return {
            **state,
            "messages": messages,
            "is_spam": is_spam,
            "current_step": "complete" if is_spam else "collect"
        }


class MockCollectNode:
    """Mock implementation of collect node."""
    
    async def __call__(self, state: Dict) -> Dict:
        """Extract customer information from messages."""
        messages = state.get("messages", [])
        
        # Initialize missing fields
        customer_name = state.get("customer_name")
        customer_goal = state.get("customer_goal")
        customer_budget = state.get("customer_budget")
        
        # Simple extraction logic
        for msg in messages:
            if hasattr(msg, 'content'):
                content = msg.content
                
                # Extract name (look for "I am" or "My name is")
                if not customer_name:
                    name_match = re.search(r'(?:I am|My name is|I\'m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', content)
                    if name_match:
                        customer_name = name_match.group(1)
                
                # Extract budget (look for dollar amounts)
                if not customer_budget:
                    budget_match = re.search(r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', content)
                    if budget_match:
                        budget_str = budget_match.group(1).replace(',', '')
                        customer_budget = float(budget_str)
                
                # Extract goal (simple keyword matching)
                if not customer_goal and any(word in content.lower() for word in ['consultation', 'marketing', 'strategy', 'help', 'advice']):
                    customer_goal = content[:100]  # First 100 chars as goal
        
        # Determine next step
        if customer_name and customer_goal and customer_budget:
            next_step = "validate"
        else:
            next_step = "collect"
        
        return {
            **state,
            "messages": messages,
            "customer_name": customer_name,
            "customer_goal": customer_goal,
            "customer_budget": customer_budget,
            "current_step": next_step
        }


class MockValidateNode:
    """Mock implementation of validate node."""
    
    def __init__(self, minimum_budget: float = 1000.0):
        self.minimum_budget = minimum_budget
    
    async def __call__(self, state: Dict) -> Dict:
        """Validate customer information."""
        validation_errors = []
        
        # Check required fields
        if not state.get("customer_name"):
            validation_errors.append("Customer name is required")
        
        if not state.get("customer_goal"):
            validation_errors.append("Customer goal is required")
        
        customer_budget = state.get("customer_budget")
        if customer_budget is None:
            validation_errors.append("Customer budget is required")
        elif customer_budget < self.minimum_budget:
            validation_errors.append(f"Budget must be at least ${self.minimum_budget}")
        
        # Determine next step
        if validation_errors:
            next_step = "collect"  # Go back to collect more info
        else:
            next_step = "book"
        
        return {
            **state,
            "validation_errors": validation_errors,
            "current_step": next_step
        }


class MockBookingNode:
    """Mock implementation of booking node."""
    
    async def __call__(self, state: Dict) -> Dict:
        """Create appointment in GHL."""
        # Simulate booking process
        appointment_time = datetime.now() + timedelta(days=random.randint(1, 7))
        
        booking_result = {
            "appointment_id": f"apt-{random.randint(1000, 9999)}",
            "contact_id": f"con-{random.randint(1000, 9999)}",
            "scheduled_time": appointment_time.isoformat(),
            "duration_minutes": 60,
            "status": "confirmed",
            "calendar_id": "cal-123",
            "location_id": "loc-456"
        }
        
        return {
            **state,
            "booking_result": booking_result,
            "current_step": "complete"
        }


class MockGHLClient:
    """Mock GoHighLevel API client."""
    
    def __init__(self):
        self.contacts = MockContactsAPI()
        self.calendars = MockCalendarsAPI()
        self.appointments = MockAppointmentsAPI()


class MockContactsAPI:
    """Mock GHL Contacts API."""
    
    async def search(self, phone: str) -> Dict:
        """Search for existing contact."""
        # Simulate some contacts exist
        if phone.endswith("000"):
            return {
                "contacts": [{
                    "id": "existing-contact-123",
                    "name": "Existing User",
                    "phone": phone
                }],
                "meta": {"total": 1}
            }
        return {"contacts": [], "meta": {"total": 0}}
    
    async def create(self, data: Dict) -> Dict:
        """Create new contact."""
        return {
            "id": f"contact-{random.randint(1000, 9999)}",
            "name": data.get("name", "Unknown"),
            "phone": data.get("phone", ""),
            "created_at": datetime.now().isoformat()
        }
    
    async def update(self, contact_id: str, data: Dict) -> Dict:
        """Update existing contact."""
        return {
            "id": contact_id,
            **data,
            "updated_at": datetime.now().isoformat()
        }


class MockCalendarsAPI:
    """Mock GHL Calendars API."""
    
    async def get_available_slots(self, calendar_id: str, start_date: str, end_date: str) -> Dict:
        """Get available appointment slots."""
        slots = []
        current = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        while current < end:
            # Add some slots (9am, 2pm, 4pm)
            for hour in [9, 14, 16]:
                slot_time = current.replace(hour=hour, minute=0, second=0)
                if slot_time > datetime.now():
                    slots.append({
                        "startTime": slot_time.isoformat(),
                        "endTime": (slot_time + timedelta(hours=1)).isoformat(),
                        "available": True
                    })
            current += timedelta(days=1)
        
        return {"slots": slots[:10]}  # Return max 10 slots


class MockAppointmentsAPI:
    """Mock GHL Appointments API."""
    
    async def create(self, data: Dict) -> Dict:
        """Create appointment."""
        return {
            "id": f"apt-{random.randint(1000, 9999)}",
            "contactId": data.get("contactId"),
            "calendarId": data.get("calendarId"),
            "startTime": data.get("startTime"),
            "endTime": data.get("endTime"),
            "title": data.get("title", "Consultation"),
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
    
    async def update(self, appointment_id: str, data: Dict) -> Dict:
        """Update appointment."""
        return {
            "id": appointment_id,
            **data,
            "updated_at": datetime.now().isoformat()
        }
    
    async def cancel(self, appointment_id: str) -> Dict:
        """Cancel appointment."""
        return {
            "id": appointment_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat()
        }


class MockLangSmithClient:
    """Mock LangSmith tracing client."""
    
    def __init__(self):
        self.runs = {}
    
    def create_run(self, name: str, run_type: str, **kwargs) -> Dict:
        """Create a new run."""
        run_id = f"run-{random.randint(1000, 9999)}"
        self.runs[run_id] = {
            "id": run_id,
            "name": name,
            "run_type": run_type,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            **kwargs
        }
        return {"run_id": run_id}
    
    def update_run(self, run_id: str, **kwargs) -> None:
        """Update run data."""
        if run_id in self.runs:
            self.runs[run_id].update(kwargs)
    
    def end_run(self, run_id: str, outputs: Any = None, error: str = None) -> None:
        """End a run."""
        if run_id in self.runs:
            self.runs[run_id].update({
                "end_time": datetime.now().isoformat(),
                "status": "error" if error else "success",
                "outputs": outputs,
                "error": error
            })


class MockWebhookSecurity:
    """Mock webhook security utilities."""
    
    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """Mock signature verification."""
        # In tests, signature ending with 'valid' is valid
        return signature.endswith('valid')
    
    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate mock signature."""
        return f"mock_sig_{secret}_valid"


class MockRateLimiter:
    """Mock rate limiter."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limit."""
        now = datetime.now()
        
        # Clean old entries
        self.requests = {
            k: v for k, v in self.requests.items()
            if (now - v).seconds < self.window_seconds
        }
        
        # Count requests for this key
        key_requests = [v for k, v in self.requests.items() if k.startswith(key)]
        
        if len(key_requests) >= self.max_requests:
            return False
        
        # Add this request
        self.requests[f"{key}_{now.timestamp()}"] = now
        return True