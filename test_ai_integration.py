#!/usr/bin/env python3
"""
Test AI integration with the 3 required inputs.
"""
import asyncio
import os
from dotenv import load_dotenv
from stateless_booking.message_processor import MessageProcessor

# Load environment
load_dotenv()


def test_ai_inputs():
    """Test AI with the 3 required inputs."""
    processor = MessageProcessor()
    
    # Test inputs
    test_cases = [
        ("Jaime", "greeting", "en", {}),
        ("Do you do automation?", "greeting", "en", {}),
        ("Hola", "greeting", "es", {})
    ]
    
    print("🤖 AI INTEGRATION TEST")
    print("=" * 60)
    
    for message, step, lang, state in test_cases:
        print(f"\n📥 INPUT: '{message}'")
        print(f"   Step: {step}, Language: {lang}")
        
        # Process message
        result = processor.process_message(message, step, lang, state)
        
        print(f"📤 AI RESPONSE: {result['response']}")
        print(f"   Next Step: {result['next_step']}")
        print(f"   Updates: {result['updates']}")
        print("-" * 40)
    
    print("\n✅ AI INTEGRATION COMPLETE!")


if __name__ == "__main__":
    test_ai_inputs()