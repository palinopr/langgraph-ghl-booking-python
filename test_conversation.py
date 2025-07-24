#!/usr/bin/env python3
"""Test the conversational collect node"""
import asyncio
import os
from langchain_core.messages import HumanMessage
from booking_agent.utils.nodes import collect_node, validate_node
from booking_agent.utils.state import BookingState

# Set environment variables for testing
os.environ["OPENAI_API_KEY"] = "sk-test-key"  # Replace with actual key for real testing


async def test_conversation():
    """Test the conversational flow"""
    
    # Test Spanish detection
    print("=== Testing Spanish Conversation ===")
    state = {
        "messages": [HumanMessage(content="Hola necesito ayuda con mi negocio")],
        "thread_id": "test-spanish"
    }
    
    # First interaction
    result = await collect_node(state)
    print(f"Bot: {result['messages'][-1].content}")
    print(f"Language detected: {result.get('language')}")
    print(f"Collection step: {result.get('collection_step')}")
    
    # User provides name
    state["messages"] = result["messages"] + [HumanMessage(content="Soy Carlos")]
    state.update(result)
    result = await collect_node(state)
    print(f"\nUser: Soy Carlos")
    print(f"Bot: {result['messages'][-1].content}")
    print(f"Extracted name: {result.get('customer_name')}")
    
    # User provides goal
    state["messages"] = result["messages"] + [HumanMessage(content="Quiero más clientes para mi restaurante")]
    state.update(result)
    result = await collect_node(state)
    print(f"\nUser: Quiero más clientes para mi restaurante")
    print(f"Bot: {result['messages'][-1].content}")
    print(f"Extracted goal: {result.get('customer_goal')}")
    
    print("\n=== Testing English Conversation ===")
    state = {
        "messages": [HumanMessage(content="Hi I need help growing my business")],
        "thread_id": "test-english"
    }
    
    # First interaction
    result = await collect_node(state)
    print(f"Bot: {result['messages'][-1].content}")
    print(f"Language detected: {result.get('language')}")
    
    # Complete flow
    state["messages"] = result["messages"] + [HumanMessage(content="I'm Sarah")]
    state.update(result)
    result = await collect_node(state)
    print(f"\nUser: I'm Sarah")
    print(f"Bot: {result['messages'][-1].content}")
    
    state["messages"] = result["messages"] + [HumanMessage(content="I want to increase online sales")]
    state.update(result)
    result = await collect_node(state)
    print(f"\nUser: I want to increase online sales")
    print(f"Bot: {result['messages'][-1].content}")
    
    state["messages"] = result["messages"] + [HumanMessage(content="My website gets traffic but no one buys")]
    state.update(result)
    result = await collect_node(state)
    print(f"\nUser: My website gets traffic but no one buys")
    print(f"Bot: {result['messages'][-1].content}")
    
    state["messages"] = result["messages"] + [HumanMessage(content="About $500 per month")]
    state.update(result)
    result = await collect_node(state)
    print(f"\nUser: About $500 per month")
    print(f"Bot: {result['messages'][-1].content}")
    print(f"Budget: ${result.get('customer_budget')}")
    
    state["messages"] = result["messages"] + [HumanMessage(content="sarah@example.com")]
    state.update(result)
    result = await collect_node(state)
    print(f"\nUser: sarah@example.com")
    print(f"Bot: {result['messages'][-1].content}")
    
    state["messages"] = result["messages"] + [HumanMessage(content="Tuesday works best")]
    state.update(result)
    result = await collect_node(state)
    print(f"\nUser: Tuesday works best")
    print(f"Current step after day selection: {result.get('current_step')}")
    
    # Test validation
    print("\n=== Testing Validation ===")
    validation_result = await validate_node(result)
    print(f"Validation passed: {len(validation_result.get('validation_errors', [])) == 0}")
    print(f"Next step: {validation_result.get('current_step')}")


if __name__ == "__main__":
    asyncio.run(test_conversation())