#!/usr/bin/env python3
"""
Test the GHL field mapping implementation.
Verifies that the stateless booking system correctly uses actual GHL field IDs.
"""
import asyncio
import os
from dotenv import load_dotenv
from stateless_booking.ghl_state_manager import GHLStateManager
from config.ghl_field_mapping import CUSTOM_FIELD_IDS, EXISTING_FIELD_IDS

# Load environment variables
load_dotenv()


async def test_field_mapping():
    """Test field mapping in GHL state manager."""
    print("Testing GHL Field Mapping")
    print("=" * 60)
    
    # Show current mapping
    print("\nCurrent Field Mapping:")
    print("-" * 40)
    
    print("\nExisting fields (with real IDs):")
    for name, field_id in EXISTING_FIELD_IDS.items():
        print(f"  {name}: {field_id}")
    
    print("\nFields to be created:")
    missing_fields = []
    for name, field_id in CUSTOM_FIELD_IDS.items():
        if name not in EXISTING_FIELD_IDS:
            missing_fields.append(name)
            print(f"  {name}: {field_id} (placeholder)")
    
    # Initialize state manager
    try:
        ghl = GHLStateManager()
        print(f"\n✅ GHL State Manager initialized successfully")
        print(f"   Using {len(EXISTING_FIELD_IDS)} existing fields")
        print(f"   Need to create {len(missing_fields)} fields")
        
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        return
    
    # Test field access
    print("\n" + "=" * 60)
    print("Field Access Test:")
    print("-" * 40)
    
    # Test that manager has field_ids attribute
    if hasattr(ghl, 'field_ids'):
        print("✅ field_ids attribute exists")
        print(f"   Total fields configured: {len(ghl.field_ids)}")
    else:
        print("❌ field_ids attribute missing")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Create the missing fields in GHL dashboard")
    print("2. Update CUSTOM_FIELD_IDS with actual IDs") 
    print("3. Run this test again to verify all fields are mapped")
    print("4. Deploy the stateless booking system")


if __name__ == "__main__":
    asyncio.run(test_field_mapping())