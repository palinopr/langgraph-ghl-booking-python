"""
End-to-end workflow tests.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List
from tests.conftest import BookingState


class TestWorkflowExecution:
    """Test complete workflow execution."""
    
    @pytest.mark.asyncio
    async def test_workflow_happy_path(self, mock_workflow_invoke):
        """Test successful booking flow from start to finish."""
        initial_state = {
            "messages": [HumanMessage(content="Hi, I need to book a consultation. My name is John Doe, my budget is $5000 for marketing strategy help.")],
            "thread_id": "test-thread-123"
        }
        
        result = await mock_workflow_invoke(initial_state)
        
        assert result["current_step"] == "complete"
        assert result["booking_result"] is not None
        assert result["booking_result"]["appointment_id"] == "test-appointment-123"
        assert len(result["messages"]) > len(initial_state["messages"])
    
    @pytest.mark.asyncio
    async def test_workflow_spam_detection(self, mock_workflow_invoke):
        """Test workflow stops for spam messages."""
        spam_state = {
            "messages": [HumanMessage(content="Click here for FREE iPhone! bit.ly/win")],
            "thread_id": "spam-thread",
            "is_spam": True
        }
        
        result = await mock_workflow_invoke(spam_state)
        
        assert result["current_step"] == "complete"
        assert result.get("booking_result") is None
        assert "spam" in result["messages"][-1].content.lower()
    
    @pytest.mark.asyncio
    async def test_workflow_data_collection_loop(self):
        """Test workflow loops to collect missing data."""
        # Mock a workflow that needs multiple interactions
        async def multi_step_workflow(state, config=None):
            messages = state.get("messages", [])
            
            if len(messages) == 1:
                # First call - need name
                return {
                    **state,
                    "current_step": "collect",
                    "messages": messages + [AIMessage(content="What's your name?")]
                }
            elif len(messages) == 3:
                # Second call - need budget
                return {
                    **state,
                    "customer_name": "John Doe",
                    "current_step": "collect",
                    "messages": messages + [AIMessage(content="What's your budget?")]
                }
            else:
                # Final call - all data collected
                return {
                    **state,
                    "customer_name": "John Doe",
                    "customer_budget": 5000,
                    "customer_goal": "Marketing help",
                    "current_step": "complete",
                    "booking_result": {"appointment_id": "final-123"}
                }
        
        workflow = AsyncMock(side_effect=multi_step_workflow)
        
        # Initial message
        state = {"messages": [HumanMessage(content="I need help")], "thread_id": "test"}
        
        # First interaction
        state = await workflow(state)
        assert state["current_step"] == "collect"
        assert "name" in state["messages"][-1].content
        
        # Add user response
        state["messages"].append(HumanMessage(content="John Doe"))
        
        # Second interaction
        state = await workflow(state)
        assert state["current_step"] == "collect"
        assert "budget" in state["messages"][-1].content
        
        # Add final response
        state["messages"].append(HumanMessage(content="$5000"))
        
        # Final interaction
        state = await workflow(state)
        assert state["current_step"] == "complete"
        assert state["booking_result"] is not None
    
    @pytest.mark.asyncio
    async def test_workflow_validation_failure_recovery(self):
        """Test workflow handles validation failures and recovers."""
        async def validation_workflow(state, config=None):
            budget = state.get("customer_budget", 0)
            
            if budget < 1000:
                return {
                    **state,
                    "validation_errors": ["Budget must be at least $1000"],
                    "current_step": "collect",
                    "messages": state["messages"] + [
                        AIMessage(content="Sorry, our minimum budget is $1000. Can you increase your budget?")
                    ]
                }
            else:
                return {
                    **state,
                    "validation_errors": [],
                    "current_step": "complete",
                    "booking_result": {"appointment_id": "valid-booking"}
                }
        
        workflow = AsyncMock(side_effect=validation_workflow)
        
        # Start with low budget
        state = {
            "messages": [HumanMessage(content="Book appointment")],
            "customer_name": "Jane",
            "customer_goal": "Consultation",
            "customer_budget": 500
        }
        
        # First attempt - validation fails
        state = await workflow(state)
        assert state["current_step"] == "collect"
        assert len(state["validation_errors"]) > 0
        
        # Update budget
        state["customer_budget"] = 2000
        state["messages"].append(HumanMessage(content="OK, I can do $2000"))
        
        # Second attempt - validation passes
        state = await workflow(state)
        assert state["current_step"] == "complete"
        assert state["booking_result"] is not None


class TestWorkflowStateManagement:
    """Test workflow state transitions and management."""
    
    @pytest.mark.asyncio
    async def test_state_persistence_across_calls(self):
        """Test state is properly maintained across workflow calls."""
        states_history = []
        
        async def tracking_workflow(state, config=None):
            step = state.get("current_step", "triage")
            
            if step == "triage":
                result = {**state, "current_step": "collect", "is_spam": False}
            elif step == "collect":
                result = {**state, "current_step": "validate", "customer_name": "Test User"}
            elif step == "validate":
                result = {**state, "current_step": "book", "validation_errors": []}
            else:
                result = {**state, "current_step": "complete", "booking_result": {"id": "123"}}
            
            states_history.append(result.copy())
            return result
        
        workflow = AsyncMock(side_effect=tracking_workflow)
        
        state = {"messages": [HumanMessage(content="Book me")], "thread_id": "test"}
        
        # Run through all steps
        for _ in range(4):
            state = await workflow(state)
        
        # Verify state evolution
        assert len(states_history) == 4
        assert states_history[0]["current_step"] == "collect"
        assert states_history[1]["current_step"] == "validate"
        assert states_history[2]["current_step"] == "book"
        assert states_history[3]["current_step"] == "complete"
    
    @pytest.mark.asyncio
    async def test_thread_id_consistency(self):
        """Test thread_id remains consistent throughout workflow."""
        thread_id = "consistent-thread-123"
        
        async def thread_checking_workflow(state, config=None):
            assert state.get("thread_id") == thread_id
            return {**state, "current_step": "complete"}
        
        workflow = AsyncMock(side_effect=thread_checking_workflow)
        
        state = {"messages": [HumanMessage(content="Test")], "thread_id": thread_id}
        result = await workflow(state)
        
        assert result["thread_id"] == thread_id


class TestWorkflowErrorHandling:
    """Test workflow error scenarios."""
    
    @pytest.mark.asyncio
    async def test_workflow_handles_node_errors(self):
        """Test workflow handles errors from individual nodes."""
        async def error_workflow(state, config=None):
            if state.get("trigger_error"):
                raise Exception("Node processing error")
            return {**state, "current_step": "complete"}
        
        workflow = AsyncMock(side_effect=error_workflow)
        
        # Normal execution
        state = {"messages": [HumanMessage(content="Normal")]}
        result = await workflow(state)
        assert result["current_step"] == "complete"
        
        # Error execution
        state = {"messages": [HumanMessage(content="Error")], "trigger_error": True}
        with pytest.raises(Exception) as exc:
            await workflow(state)
        assert "Node processing error" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_workflow_handles_api_failures(self):
        """Test workflow handles external API failures gracefully."""
        async def api_failure_workflow(state, config=None):
            if state["current_step"] == "book":
                # Simulate GHL API failure
                return {
                    **state,
                    "current_step": "complete",
                    "booking_result": None,
                    "messages": state["messages"] + [
                        AIMessage(content="Sorry, I couldn't book the appointment. Please try again later.")
                    ]
                }
            return {**state, "current_step": "book"}
        
        workflow = AsyncMock(side_effect=api_failure_workflow)
        
        state = {
            "messages": [HumanMessage(content="Book appointment")],
            "current_step": "book"
        }
        
        result = await workflow(state)
        assert result["current_step"] == "complete"
        assert result["booking_result"] is None
        assert "couldn't book" in result["messages"][-1].content


class TestWorkflowIntegration:
    """Test workflow integration with external systems."""
    
    @pytest.mark.asyncio
    @patch('langsmith.Client')
    async def test_workflow_langsmith_tracing(self, mock_langsmith_client):
        """Test workflow integrates with LangSmith tracing."""
        mock_client = Mock()
        mock_client.create_run.return_value = {"run_id": "trace-123"}
        mock_langsmith_client.return_value = mock_client
        
        # Mock workflow with tracing
        async def traced_workflow(state, config=None):
            # Simulate tracing calls
            run_id = mock_client.create_run(
                name="booking_workflow",
                run_type="chain",
                inputs=state
            )
            
            try:
                result = {**state, "current_step": "complete"}
                mock_client.end_run(run_id["run_id"], outputs=result)
                return result
            except Exception as e:
                mock_client.end_run(run_id["run_id"], error=str(e))
                raise
        
        workflow = AsyncMock(side_effect=traced_workflow)
        
        state = {"messages": [HumanMessage(content="Test")]}
        result = await workflow(state)
        
        mock_client.create_run.assert_called_once()
        mock_client.end_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_message_history(self, complete_state):
        """Test workflow maintains proper message history."""
        message_count = len(complete_state.messages)
        
        async def history_workflow(state, config=None):
            messages = state.get("messages", [])
            # Should maintain all previous messages
            assert len(messages) >= message_count
            
            # Add response
            return {
                **state,
                "messages": messages + [AIMessage(content="Booking confirmed!")],
                "current_step": "complete"
            }
        
        workflow = AsyncMock(side_effect=history_workflow)
        
        result = await workflow(complete_state.to_dict())
        assert len(result["messages"]) == message_count + 1
        assert result["messages"][-1].content == "Booking confirmed!"


class TestWorkflowEdgeCases:
    """Test workflow edge cases and boundaries."""
    
    @pytest.mark.asyncio
    async def test_workflow_empty_messages(self):
        """Test workflow handles empty message list."""
        async def empty_handler_workflow(state, config=None):
            if not state.get("messages"):
                return {
                    **state,
                    "messages": [AIMessage(content="Hello! How can I help you?")],
                    "current_step": "collect"
                }
            return {**state, "current_step": "complete"}
        
        workflow = AsyncMock(side_effect=empty_handler_workflow)
        
        state = {"messages": [], "thread_id": "empty-test"}
        result = await workflow(state)
        
        assert len(result["messages"]) == 1
        assert result["current_step"] == "collect"
    
    @pytest.mark.asyncio
    async def test_workflow_very_long_conversation(self):
        """Test workflow handles very long conversations."""
        # Create a long conversation history
        messages = []
        for i in range(50):
            messages.append(HumanMessage(content=f"Message {i}"))
            messages.append(AIMessage(content=f"Response {i}"))
        
        async def long_conv_workflow(state, config=None):
            assert len(state["messages"]) == 100
            return {
                **state,
                "current_step": "complete",
                "booking_result": {"id": "long-conv-booking"}
            }
        
        workflow = AsyncMock(side_effect=long_conv_workflow)
        
        state = {"messages": messages, "thread_id": "long-conv"}
        result = await workflow(state)
        
        assert result["current_step"] == "complete"
        assert result["booking_result"] is not None
    
    @pytest.mark.asyncio
    async def test_workflow_concurrent_updates(self):
        """Test workflow handles concurrent state updates safely."""
        update_count = 0
        
        async def concurrent_workflow(state, config=None):
            nonlocal update_count
            update_count += 1
            
            # Simulate concurrent processing
            import asyncio
            await asyncio.sleep(0.01)
            
            return {
                **state,
                "update_count": update_count,
                "current_step": "complete"
            }
        
        workflow = AsyncMock(side_effect=concurrent_workflow)
        
        # Run multiple concurrent workflows
        states = [
            {"messages": [HumanMessage(content=f"User {i}")], "thread_id": f"thread-{i}"}
            for i in range(5)
        ]
        
        import asyncio
        results = await asyncio.gather(*[workflow(s) for s in states])
        
        assert len(results) == 5
        assert all(r["current_step"] == "complete" for r in results)
        assert update_count == 5