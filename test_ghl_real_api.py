#!/usr/bin/env python3
"""Test GHL API with REAL credentials."""

import os
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from booking_agent.utils.tools import GHLClient
import json

# Load environment variables
load_dotenv()

# Set real GHL credentials
os.environ["GHL_API_KEY"] = "pit-21cee867-6a57-4eea-b6fa-2bd4462934d0"
os.environ["GHL_LOCATION_ID"] = "sHFG9Rw6BdGh6d6bfMqG"
os.environ["GHL_CALENDAR_ID"] = "eIHCWiTQjE1lTzjdz4xi"


async def test_create_contact():
    """Test 1: Create a test contact."""
    print("\n🧪 Test 1: Creating test contact...")
    
    client = GHLClient()
    
    # Create test contact with unique email and phone using timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Generate unique phone by using last 4 digits of timestamp
    phone_suffix = timestamp[-4:]
    contact = await client.create_contact(
        name="Rachel Test GHL",
        phone=f"+1213555{phone_suffix}",
        email=f"rachel.test.{timestamp}@aioutletmedia.com",
        tags=["test_contact", "api_test", "whatsapp_lead"]
    )
    
    print(f"✅ Contact created successfully!")
    print(f"   Raw response: {json.dumps(contact, indent=2)}")
    
    # Try different field names
    contact_id = contact.get('id') or contact.get('contact', {}).get('id') or contact.get('contactId')
    name = contact.get('name') or contact.get('contact', {}).get('name') or contact.get('firstName')
    
    print(f"   - Contact ID: {contact_id}")
    print(f"   - Name: {name}")
    print(f"   - Phone: {contact.get('phone') or contact.get('contact', {}).get('phone')}")
    print(f"   - Email: {contact.get('email') or contact.get('contact', {}).get('email')}")
    print(f"   - Tags: {contact.get('tags', [])}")
    
    return contact_id


async def test_get_available_slots():
    """Test 2: Get REAL calendar slots."""
    print("\n🧪 Test 2: Getting real calendar slots...")
    
    client = GHLClient()
    
    # Test for different days
    days = ["Tuesday", "Wednesday", "Thursday", "Friday"]
    
    for day in days:
        print(f"\n   📅 Checking {day}:")
        slots = await client.get_available_slots_for_day(
            calendar_id=os.getenv("GHL_CALENDAR_ID"),
            day_name=day,
            duration_minutes=30
        )
        
        if slots:
            print(f"   ✅ Found {len(slots)} available slots:")
            for i, slot in enumerate(slots[:3]):  # Show first 3 slots
                print(f"      - {slot['display']} ({slot['start'].strftime('%Y-%m-%d')})")
        else:
            print(f"   ⚠️  No slots available on {day}")
    
    return slots


async def test_create_appointment(contact_id: str, slots: list):
    """Test 3: Book a REAL appointment."""
    print("\n🧪 Test 3: Creating real appointment...")
    
    if not slots:
        print("   ❌ No available slots to book!")
        return None
    
    client = GHLClient()
    
    # Use the first available slot
    slot = slots[0]
    
    # Create appointment
    appointment = await client.create_appointment(
        contact_id=contact_id,
        calendar_id=os.getenv("GHL_CALENDAR_ID"),
        start_time=slot["start"],
        end_time=slot["end"],
        title="Fitness Consultation - Rachel Test",
        notes="Goal: Weight loss\nBudget: $2500/month\nPain Point: Can't seem to lose the last 10 pounds\nSource: WhatsApp Bot Test"
    )
    
    print(f"✅ Appointment created successfully!")
    print(f"   - Appointment ID: {appointment.get('id')}")
    print(f"   - Title: {appointment.get('title')}")
    print(f"   - Start: {slot['start'].strftime('%A, %B %d at %I:%M %p')}")
    print(f"   - Status: {appointment.get('status')}")
    
    return appointment


async def test_full_booking_flow():
    """Test complete booking flow with real API."""
    print("\n🚀 TESTING COMPLETE GHL BOOKING FLOW WITH REAL API")
    print("=" * 60)
    
    try:
        # Test 1: Create contact
        contact_id = await test_create_contact()
        
        if not contact_id:
            print("\n❌ Failed to create contact. Stopping tests.")
            return
        
        # Test 2: Get available slots
        slots = await test_get_available_slots()
        
        # Test 3: Create appointment
        if slots and contact_id:
            appointment = await test_create_appointment(contact_id, slots)
            
            if appointment:
                print("\n✅ ALL TESTS PASSED!")
                print("\n📋 Summary:")
                print(f"   - Contact ID: {contact_id}")
                print(f"   - Appointment ID: {appointment.get('id')}")
                print(f"   - Appointment Time: {slots[0]['start'].strftime('%A, %B %d at %I:%M %p')}")
                print("\n🎯 Please verify in GHL dashboard:")
                print("   1. Go to Contacts and search for 'Rachel Test GHL'")
                print("   2. Go to Calendar and verify the appointment appears")
                print("   3. Check that tags and notes are properly saved")
        else:
            print("\n⚠️  Tests completed with warnings - no appointment created")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔧 GHL Real API Testing Tool")
    print("Using REAL credentials:")
    print(f"   - API Key: {os.getenv('GHL_API_KEY')[:10]}...")
    print(f"   - Location ID: {os.getenv('GHL_LOCATION_ID')}")
    print(f"   - Calendar ID: {os.getenv('GHL_CALENDAR_ID')}")
    
    asyncio.run(test_full_booking_flow())