"""
Shared fixtures and configuration for tests.
"""
import pytest
import pytest_asyncio
from typing import Dict, List, Optional
from unittest.mock import Mock, AsyncMock, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from datetime import datetime


# Mock BookingState type since implementation may not exist yet
class BookingState:
    """Mock BookingState for testing."""
    def __init__(self, 
                 messages: List[BaseMessage] = None,
                 customer_name: Optional[str] = None,
                 customer_goal: Optional[str] = None,
                 customer_budget: Optional[float] = None,
                 current_step: str = "triage",
                 is_spam: bool = False,
                 validation_errors: List[str] = None,
                 booking_result: Optional[dict] = None,
                 thread_id: str = "test-thread-123"):
        self.messages = messages or []
        self.customer_name = customer_name
        self.customer_goal = customer_goal
        self.customer_budget = customer_budget
        self.current_step = current_step
        self.is_spam = is_spam
        self.validation_errors = validation_errors or []
        self.booking_result = booking_result
        self.thread_id = thread_id
    
    def to_dict(self):
        """Convert to dictionary for testing."""
        return {
            "messages": self.messages,
            "customer_name": self.customer_name,
            "customer_goal": self.customer_goal,
            "customer_budget": self.customer_budget,
            "current_step": self.current_step,
            "is_spam": self.is_spam,
            "validation_errors": self.validation_errors,
            "booking_result": self.booking_result,
            "thread_id": self.thread_id
        }


@pytest.fixture
def mock_state():
    """Provide a mock BookingState instance."""
    return BookingState(
        messages=[HumanMessage(content="I need to book an appointment")],
        thread_id="test-thread-123"
    )


@pytest.fixture
def complete_state():
    """Provide a complete BookingState with all customer data."""
    return BookingState(
        messages=[
            HumanMessage(content="I need to book an appointment"),
            AIMessage(content="Sure! What's your name?"),
            HumanMessage(content="John Doe"),
            AIMessage(content="What's your goal?"),
            HumanMessage(content="Marketing strategy consultation"),
            AIMessage(content="What's your budget?"),
            HumanMessage(content="$5000")
        ],
        customer_name="John Doe",
        customer_goal="Marketing strategy consultation",
        customer_budget=5000.0,
        current_step="validate",
        thread_id="test-thread-456"
    )


@pytest.fixture
def spam_state():
    """Provide a spam BookingState."""
    return BookingState(
        messages=[HumanMessage(content="Click here for free iPhone! bit.ly/scam123")],
        is_spam=True,
        current_step="triage",
        thread_id="spam-thread-789"
    )


@pytest.fixture
def invalid_budget_state():
    """Provide a state with budget below minimum."""
    return BookingState(
        messages=[HumanMessage(content="I want to book with $500 budget")],
        customer_name="Jane Smith",
        customer_goal="Quick consultation",
        customer_budget=500.0,
        current_step="validate",
        thread_id="low-budget-thread"
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for LLM calls."""
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock(
        return_value=Mock(
            choices=[Mock(
                message=Mock(content="Extracted: Name: John Doe, Goal: Marketing, Budget: 5000")
            )]
        )
    )
    return mock


@pytest.fixture
def mock_ghl_client():
    """Mock GoHighLevel client."""
    mock = AsyncMock()
    
    # Mock contact search
    mock.contacts.search = AsyncMock(return_value={
        "contacts": [],
        "meta": {"total": 0}
    })
    
    # Mock contact creation
    mock.contacts.create = AsyncMock(return_value={
        "id": "contact-123",
        "name": "John Doe",
        "phone": "+1234567890"
    })
    
    # Mock appointment booking
    mock.calendars.appointments.create = AsyncMock(return_value={
        "id": "appointment-123",
        "startTime": "2024-01-15T10:00:00Z",
        "endTime": "2024-01-15T11:00:00Z",
        "status": "confirmed"
    })
    
    # Mock calendar availability
    mock.calendars.get_available_slots = AsyncMock(return_value={
        "slots": [
            {"startTime": "2024-01-15T10:00:00Z", "endTime": "2024-01-15T11:00:00Z"},
            {"startTime": "2024-01-15T14:00:00Z", "endTime": "2024-01-15T15:00:00Z"}
        ]
    })
    
    return mock


@pytest.fixture
def mock_langsmith_client():
    """Mock LangSmith client for tracing."""
    mock = Mock()
    mock.create_run = Mock(return_value={"run_id": "test-run-123"})
    mock.update_run = Mock()
    mock.end_run = Mock()
    return mock


@pytest.fixture
def webhook_payload():
    """Sample webhook payload."""
    return {
        "message": "I need to book an appointment",
        "phone": "+1234567890",
        "thread_id": "webhook-thread-123"
    }


@pytest.fixture
def mock_workflow_invoke():
    """Mock for workflow invocation."""
    async def _invoke(state, config=None):
        # Simulate workflow progression
        if state.get("is_spam"):
            return {
                **state,
                "current_step": "complete",
                "messages": state["messages"] + [
                    AIMessage(content="Message identified as spam.")
                ]
            }
        
        # Simulate successful booking flow
        return {
            **state,
            "current_step": "complete",
            "booking_result": {
                "appointment_id": "test-appointment-123",
                "scheduled_time": "2024-01-15T10:00:00Z"
            },
            "messages": state["messages"] + [
                AIMessage(content="Appointment booked successfully!")
            ]
        }
    
    return AsyncMock(side_effect=_invoke)


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return {
        "business": {
            "name": "Test Business",
            "minimum_budget": 1000,
            "timezone": "PST"
        },
        "ghl": {
            "calendar_id": "test-calendar-123",
            "location_id": "test-location-456"
        }
    }


@pytest_asyncio.fixture
async def async_mock_state():
    """Async fixture for mock state."""
    return BookingState(
        messages=[HumanMessage(content="Async test message")],
        thread_id="async-test-thread"
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Test utilities
class MockLangGraphNode:
    """Mock LangGraph node for testing."""
    def __init__(self, name: str, func: callable = None):
        self.name = name
        self.func = func or AsyncMock()
    
    async def __call__(self, state: Dict):
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(state)
        return self.func(state)


def create_mock_message(content: str, role: str = "human") -> BaseMessage:
    """Create a mock message for testing."""
    if role == "human":
        return HumanMessage(content=content)
    elif role == "ai":
        return AIMessage(content=content)
    else:
        raise ValueError(f"Unknown role: {role}")


# Import asyncio for async tests
import asyncio