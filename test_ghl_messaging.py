#!/usr/bin/env python3
"""Test GHL messaging integration."""

import asyncio
import os
from booking_agent.utils.tools import GHLClient

async def test_send_message():
    """Test sending a message via GHL API."""
    print("Testing GHL Message Sending...")
    
    # Initialize client
    client = GHLClient()
    
    # Use existing contact ID from error message
    contact_id = "q8hVi7cZzg3ikt6YsoiC"
    print(f"\n1. Using existing contact: {contact_id}")
    
    # Send a test message
    print("\n2. Sending test message...")
    result = await client.send_message(
        contact_id=contact_id,
        message="This is a test message from the booking system!"
    )
    
    if "error" in result:
        print(f"✗ Error sending message: {result['error']}")
    else:
        print(f"✓ Message sent successfully!")
        print(f"  Response: {result}")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run test
    asyncio.run(test_send_message())