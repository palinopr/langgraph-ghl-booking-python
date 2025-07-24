#!/usr/bin/env python3
"""
Query GHL API to get existing custom fields for our location.
This will help us map field names to actual GHL field IDs.
"""
import asyncio
import os
import aiohttp
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GHL_API_KEY")
LOCATION_ID = os.getenv("GHL_LOCATION_ID")
BASE_URL = "https://services.leadconnectorhq.com"


async def get_custom_fields():
    """Query GHL API for existing custom fields."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    
    print(f"Querying custom fields for location: {LOCATION_ID}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Get custom fields for location
        url = f"{BASE_URL}/locations/{LOCATION_ID}/customFields"
        
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                custom_fields = data.get("customFields", [])
                
                print(f"\nFound {len(custom_fields)} custom fields:\n")
                
                # Analyze fields for booking system
                booking_fields_needed = {
                    "booking_step": None,
                    "language": None,
                    "customer_name": None,
                    "customer_goal": None,
                    "customer_pain_point": None,
                    "customer_budget": None,
                    "customer_email": None,
                    "preferred_day": None,
                    "preferred_time": None,
                    "appointment_id": None,
                    "conversation_started": None
                }
                
                # Display all custom fields
                for i, field in enumerate(custom_fields, 1):
                    print(f"{i}. Field Details:")
                    print(f"   ID: {field.get('id')}")
                    print(f"   Name: {field.get('name')}")
                    print(f"   Field Key: {field.get('fieldKey')}")
                    print(f"   Type: {field.get('dataType')}")
                    print(f"   Position: {field.get('position')}")
                    
                    # Check if this matches any of our needed fields
                    field_name = field.get('name', '').lower()
                    field_key = field.get('fieldKey', '').lower()
                    
                    for needed_field in booking_fields_needed:
                        if needed_field in field_name or needed_field in field_key:
                            booking_fields_needed[needed_field] = field.get('id')
                            print(f"   ✅ MATCHES: {needed_field}")
                    
                    print()
                
                # Summary of mapping
                print("\n" + "=" * 60)
                print("BOOKING SYSTEM FIELD MAPPING:")
                print("=" * 60)
                
                fields_found = 0
                fields_missing = []
                
                for field_name, field_id in booking_fields_needed.items():
                    if field_id:
                        print(f"✅ {field_name}: '{field_id}'")
                        fields_found += 1
                    else:
                        print(f"❌ {field_name}: NOT FOUND")
                        fields_missing.append(field_name)
                
                print(f"\nSummary: {fields_found}/{len(booking_fields_needed)} fields found")
                
                if fields_missing:
                    print(f"\nFields that need to be created in GHL:")
                    for field in fields_missing:
                        print(f"  - {field}")
                
                # Generate code snippet
                if fields_found > 0:
                    print("\n" + "=" * 60)
                    print("CODE SNIPPET FOR FIELD MAPPING:")
                    print("=" * 60)
                    print("\n# Add this to your GHL configuration:")
                    print("CUSTOM_FIELD_IDS = {")
                    for field_name, field_id in booking_fields_needed.items():
                        if field_id:
                            print(f'    "{field_name}": "{field_id}",')
                    print("}")
                
                return custom_fields
                
            else:
                error = await resp.text()
                print(f"❌ Error fetching custom fields: {resp.status}")
                print(f"   Response: {error}")
                return []


async def create_missing_fields():
    """Provide instructions for creating missing fields."""
    print("\n" + "=" * 60)
    print("INSTRUCTIONS FOR CREATING MISSING FIELDS:")
    print("=" * 60)
    print("""
1. Log into GoHighLevel
2. Go to Settings > Custom Fields
3. Create the following fields:

   booking_step (Dropdown):
   - Options: greeting, name, goal, pain, budget, email, day, time, scheduled, complete
   
   language (Dropdown):
   - Options: en, es
   
   customer_name (Text)
   customer_goal (Text)
   customer_pain_point (Text)
   customer_budget (Number)
   customer_email (Email)
   preferred_day (Text)
   preferred_time (Text)
   appointment_id (Text)
   conversation_started (Date/Time)

4. After creating, run this script again to get the field IDs
""")


async def main():
    print("GHL Custom Fields Query Tool")
    print("=" * 60)
    print(f"API Key: {API_KEY[:10]}..." if API_KEY else "NOT SET")
    print(f"Location ID: {LOCATION_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60 + "\n")
    
    if not API_KEY or not LOCATION_ID:
        print("❌ ERROR: Missing GHL_API_KEY or GHL_LOCATION_ID in .env")
        return
    
    fields = await get_custom_fields()
    
    if not fields:
        await create_missing_fields()


if __name__ == "__main__":
    asyncio.run(main())