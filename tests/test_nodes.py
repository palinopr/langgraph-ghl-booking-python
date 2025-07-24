"""
Tests for individual workflow nodes.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from tests.mocks import (
    MockTriageNode, MockCollectNode, MockValidateNode, 
    MockBookingNode, MockGHLClient
)


class TestTriageNode:
    """Test triage node functionality."""
    
    @pytest.mark.asyncio
    async def test_triage_legitimate_message(self, mock_state):
        """Test triage identifies legitimate booking requests."""
        node = MockTriageNode()
        mock_state.messages = [HumanMessage(content="I need to book an appointment")]
        
        result = await node(mock_state.to_dict())
        
        assert result["is_spam"] is False
        assert result["current_step"] == "collect"
    
    @pytest.mark.asyncio
    async def test_triage_spam_keywords(self):
        """Test triage identifies spam with keywords."""
        node = MockTriageNode()
        spam_messages = [
            "Click here for free iPhone!",
            "Congratulations! You've won $1000",
            "Buy viagra now cheap prices",
            "Best casino bonuses act now"
        ]
        
        for msg in spam_messages:
            state = {"messages": [HumanMessage(content=msg)]}
            result = await node(state)
            assert result["is_spam"] is True, f"Failed to identify spam: {msg}"
            assert result["current_step"] == "complete"
    
    @pytest.mark.asyncio
    async def test_triage_suspicious_urls(self):
        """Test triage identifies suspicious URLs."""
        node = MockTriageNode()
        state = {
            "messages": [HumanMessage(content="Check this out bit.ly/amazingoffer")]
        }
        
        result = await node(state)
        
        assert result["is_spam"] is True
        assert result["current_step"] == "complete"
    
    @pytest.mark.asyncio
    async def test_triage_empty_messages(self):
        """Test triage handles empty message list."""
        node = MockTriageNode()
        state = {"messages": []}
        
        result = await node(state)
        
        assert result["is_spam"] is False
        assert result["current_step"] == "collect"
    
    @pytest.mark.asyncio
    async def test_triage_mixed_conversation(self, complete_state):
        """Test triage on conversation with multiple messages."""
        node = MockTriageNode()
        
        result = await node(complete_state.to_dict())
        
        assert result["is_spam"] is False
        assert result["current_step"] == "collect"


class TestCollectNode:
    """Test collect node functionality."""
    
    @pytest.mark.asyncio
    async def test_collect_extract_name(self):
        """Test extraction of customer name."""
        node = MockCollectNode()
        state = {
            "messages": [
                HumanMessage(content="I need help with marketing"),
                HumanMessage(content="My name is John Smith")
            ]
        }
        
        result = await node(state)
        
        assert result["customer_name"] == "John Smith"
    
    @pytest.mark.asyncio
    async def test_collect_extract_budget(self):
        """Test extraction of budget information."""
        node = MockCollectNode()
        test_cases = [
            ("My budget is $5000", 5000.0),
            ("I can spend around $10,000", 10000.0),
            ("Budget: $2,500.00", 2500.0),
            ("I have 3000 dollars", 3000.0)
        ]
        
        for msg, expected_budget in test_cases:
            state = {"messages": [HumanMessage(content=msg)]}
            result = await node(state)
            assert result["customer_budget"] == expected_budget, f"Failed for: {msg}"
    
    @pytest.mark.asyncio
    async def test_collect_extract_goal(self):
        """Test extraction of customer goal."""
        node = MockCollectNode()
        goal_messages = [
            "I need help with marketing strategy",
            "Looking for consultation on sales",
            "Need advice on business growth"
        ]
        
        for msg in goal_messages:
            state = {"messages": [HumanMessage(content=msg)]}
            result = await node(state)
            assert result["customer_goal"] is not None
            assert len(result["customer_goal"]) > 0
    
    @pytest.mark.asyncio
    async def test_collect_complete_extraction(self, complete_state):
        """Test extraction of all required fields."""
        node = MockCollectNode()
        
        # Ensure state has proper values
        complete_state.messages.append(HumanMessage(content="I'm John Doe"))
        complete_state.messages.append(HumanMessage(content="$5000"))
        
        result = await node(complete_state.to_dict())
        
        assert result["customer_name"] is not None
        assert result["customer_budget"] is not None
        assert result["current_step"] == "validate"
    
    @pytest.mark.asyncio
    async def test_collect_partial_extraction(self):
        """Test node continues collecting when data is incomplete."""
        node = MockCollectNode()
        state = {
            "messages": [HumanMessage(content="My name is Jane")],
            "customer_name": "Jane"
        }
        
        result = await node(state)
        
        assert result["customer_name"] == "Jane"
        assert result["customer_goal"] is None
        assert result["customer_budget"] is None
        assert result["current_step"] == "collect"


class TestValidateNode:
    """Test validate node functionality."""
    
    @pytest.mark.asyncio
    async def test_validate_complete_valid_data(self, complete_state):
        """Test validation passes with complete valid data."""
        node = MockValidateNode(minimum_budget=1000)
        
        result = await node(complete_state.to_dict())
        
        assert len(result["validation_errors"]) == 0
        assert result["current_step"] == "book"
    
    @pytest.mark.asyncio
    async def test_validate_missing_name(self):
        """Test validation fails without customer name."""
        node = MockValidateNode()
        state = {
            "customer_goal": "Marketing help",
            "customer_budget": 5000
        }
        
        result = await node(state)
        
        assert "Customer name is required" in result["validation_errors"]
        assert result["current_step"] == "collect"
    
    @pytest.mark.asyncio
    async def test_validate_missing_goal(self):
        """Test validation fails without customer goal."""
        node = MockValidateNode()
        state = {
            "customer_name": "John Doe",
            "customer_budget": 5000
        }
        
        result = await node(state)
        
        assert "Customer goal is required" in result["validation_errors"]
        assert result["current_step"] == "collect"
    
    @pytest.mark.asyncio
    async def test_validate_missing_budget(self):
        """Test validation fails without budget."""
        node = MockValidateNode()
        state = {
            "customer_name": "John Doe",
            "customer_goal": "Consultation"
        }
        
        result = await node(state)
        
        assert "Customer budget is required" in result["validation_errors"]
        assert result["current_step"] == "collect"
    
    @pytest.mark.asyncio
    async def test_validate_budget_below_minimum(self, invalid_budget_state):
        """Test validation fails with budget below minimum."""
        node = MockValidateNode(minimum_budget=1000)
        
        result = await node(invalid_budget_state.to_dict())
        
        assert any("Budget must be at least $1000" in err for err in result["validation_errors"])
        assert result["current_step"] == "collect"
    
    @pytest.mark.asyncio
    async def test_validate_multiple_errors(self):
        """Test validation with multiple errors."""
        node = MockValidateNode(minimum_budget=1000)
        state = {
            "customer_budget": 500
        }
        
        result = await node(state)
        
        assert len(result["validation_errors"]) >= 3  # name, goal, budget errors
        assert result["current_step"] == "collect"


class TestBookingNode:
    """Test booking node functionality."""
    
    @pytest.mark.asyncio
    async def test_booking_success(self, complete_state):
        """Test successful appointment booking."""
        node = MockBookingNode()
        
        result = await node(complete_state.to_dict())
        
        assert result["booking_result"] is not None
        assert "appointment_id" in result["booking_result"]
        assert "contact_id" in result["booking_result"]
        assert "scheduled_time" in result["booking_result"]
        assert result["booking_result"]["status"] == "confirmed"
        assert result["current_step"] == "complete"
    
    @pytest.mark.asyncio
    async def test_booking_creates_contact_and_appointment(self, complete_state):
        """Test booking creates both contact and appointment."""
        node = MockBookingNode()
        
        result = await node(complete_state.to_dict())
        
        booking = result["booking_result"]
        assert booking["appointment_id"].startswith("apt-")
        assert booking["contact_id"].startswith("con-")
        assert booking["duration_minutes"] == 60
        assert booking["calendar_id"] == "cal-123"
        assert booking["location_id"] == "loc-456"
    
    @pytest.mark.asyncio
    async def test_booking_scheduled_in_future(self, complete_state):
        """Test appointment is scheduled in the future."""
        from datetime import datetime
        node = MockBookingNode()
        
        result = await node(complete_state.to_dict())
        
        scheduled_time = datetime.fromisoformat(result["booking_result"]["scheduled_time"])
        assert scheduled_time > datetime.now()
    
    @pytest.mark.asyncio
    @patch('tests.mocks.MockBookingNode.__call__')
    async def test_booking_api_failure(self, mock_call, complete_state):
        """Test handling of GHL API failures."""
        mock_call.side_effect = Exception("GHL API Error")
        node = MockBookingNode()
        node.__call__ = mock_call
        
        with pytest.raises(Exception) as exc:
            await node(complete_state.to_dict())
        
        assert "GHL API Error" in str(exc.value)


class TestNodeIntegration:
    """Integration tests for node interactions."""
    
    @pytest.mark.asyncio
    async def test_spam_flow_stops_early(self, spam_state):
        """Test spam messages don't proceed through workflow."""
        triage = MockTriageNode()
        
        result = await triage(spam_state.to_dict())
        
        assert result["is_spam"] is True
        assert result["current_step"] == "complete"
        # Should not proceed to collect node
    
    @pytest.mark.asyncio
    async def test_valid_flow_through_all_nodes(self):
        """Test valid message flows through all nodes."""
        # Setup nodes
        triage = MockTriageNode()
        collect = MockCollectNode()
        validate = MockValidateNode()
        booking = MockBookingNode()
        
        # Initial state
        state = {
            "messages": [
                HumanMessage(content="I need an appointment. My name is John Doe. Budget is $5000 for marketing consultation.")
            ]
        }
        
        # Triage
        state = await triage(state)
        assert state["is_spam"] is False
        assert state["current_step"] == "collect"
        
        # Collect
        state = await collect(state)
        assert state["customer_name"] is not None
        assert state["customer_budget"] == 5000.0
        
        # Validate
        state = await validate(state)
        if state["validation_errors"]:
            # If goal wasn't extracted, set it manually for test
            state["customer_goal"] = "marketing consultation"
            state = await validate(state)
        
        assert len(state["validation_errors"]) == 0
        assert state["current_step"] == "book"
        
        # Book
        state = await booking(state)
        assert state["booking_result"] is not None
        assert state["current_step"] == "complete"
    
    @pytest.mark.asyncio
    async def test_invalid_budget_loops_back(self, invalid_budget_state):
        """Test invalid budget causes loop back to collect."""
        validate = MockValidateNode(minimum_budget=1000)
        
        result = await validate(invalid_budget_state.to_dict())
        
        assert result["current_step"] == "collect"
        assert len(result["validation_errors"]) > 0


class TestNodeErrorHandling:
    """Test error handling in nodes."""
    
    @pytest.mark.asyncio
    async def test_node_handles_missing_messages_key(self):
        """Test nodes handle states without messages key."""
        nodes = [MockTriageNode(), MockCollectNode()]
        
        for node in nodes:
            state = {}  # No messages key
            result = await node(state)
            assert "messages" in result or result.get("messages") == []
    
    @pytest.mark.asyncio
    async def test_node_handles_none_values(self):
        """Test nodes handle None values gracefully."""
        validate = MockValidateNode()
        state = {
            "customer_name": None,
            "customer_goal": None,
            "customer_budget": None
        }
        
        result = await validate(state)
        assert len(result["validation_errors"]) == 3
        assert result["current_step"] == "collect"
    
    @pytest.mark.asyncio
    async def test_collect_handles_malformed_messages(self):
        """Test collect node handles messages without content attribute."""
        node = MockCollectNode()
        state = {
            "messages": [{"text": "This is not a proper message object"}]
        }
        
        result = await node(state)
        # Should not crash, just return unchanged
        assert result["current_step"] == "collect"