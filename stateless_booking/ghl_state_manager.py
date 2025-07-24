"""
GHL State Manager - Handles all GoHighLevel interactions.
Reads and writes conversation state to GHL custom fields.
"""
import os
import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ghl_field_mapping import CUSTOM_FIELD_IDS

logger = logging.getLogger(__name__)


class GHLStateManager:
    """Manages conversation state in GoHighLevel."""
    
    def __init__(self):
        self.api_key = os.getenv("GHL_API_KEY")
        self.location_id = os.getenv("GHL_LOCATION_ID")
        self.base_url = "https://services.leadconnectorhq.com"
        
        if not self.api_key or not self.location_id:
            raise ValueError("GHL_API_KEY and GHL_LOCATION_ID required")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
        
        # Field ID mapping
        self.field_ids = CUSTOM_FIELD_IDS
    
    async def get_or_create_contact(self, phone: str) -> Dict[str, Any]:
        """Get existing contact or create new one."""
        async with aiohttp.ClientSession() as session:
            # Search for existing contact by phone
            search_url = f"{self.base_url}/contacts/search/duplicate"
            params = {
                "locationId": self.location_id,
                "number": phone  # Use 'number' param for phone search
            }
            
            async with session.get(search_url, headers=self.headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    contact = data.get("contact")
                    if contact:
                        logger.info(f"Found existing contact: {contact.get('id')}")
                        return contact
            
            # Create new contact
            create_url = f"{self.base_url}/contacts/"
            body = {
                "locationId": self.location_id,
                "phone": phone,
                "customFields": [
                    {"id": self.field_ids["booking_step"], "value": "greeting"},
                    {"id": self.field_ids["conversation_started"], "value": datetime.utcnow().isoformat()}
                ]
            }
            
            async with session.post(create_url, headers=self.headers, json=body) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    return data.get("contact", data)
                elif resp.status == 400:
                    # Handle duplicate contact error
                    error_data = await resp.json()
                    error_msg = error_data.get("message", "")
                    
                    # Extract contactId from error message if it exists
                    if "contactId:" in error_msg:
                        contact_id = error_msg.split("contactId:")[1].strip()
                        logger.info(f"Contact already exists with ID: {contact_id}")
                        
                        # Fetch the existing contact
                        get_url = f"{self.base_url}/contacts/{contact_id}"
                        async with session.get(get_url, headers=self.headers) as get_resp:
                            if get_resp.status == 200:
                                data = await get_resp.json()
                                return data.get("contact", data)
                    
                    # If we can't extract ID, log and raise
                    logger.error(f"Duplicate contact but couldn't extract ID: {error_msg}")
                    raise Exception(f"Contact exists but couldn't retrieve: {error_msg}")
                else:
                    error = await resp.text()
                    raise Exception(f"Failed to create contact: {resp.status} - {error}")
    
    async def get_conversation_state(self, contact_id: str) -> Dict[str, Any]:
        """Get current conversation state from contact custom fields."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/contacts/{contact_id}"
            
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    contact = data.get("contact", data)
                    custom_fields_array = contact.get("customFields", [])
                    
                    # Convert array to dict for easier access
                    custom_fields = {}
                    for field in custom_fields_array:
                        if isinstance(field, dict) and "id" in field and "value" in field:
                            custom_fields[field["id"]] = field["value"]
                    
                    # Extract conversation state - map from GHL IDs to logical names
                    state = {}
                    for logical_name, ghl_id in self.field_ids.items():
                        # Skip fields that are still placeholders
                        if ghl_id in custom_fields:
                            state[logical_name] = custom_fields[ghl_id]
                        elif logical_name == "booking_step":
                            state["booking_step"] = "greeting"  # Default
                        elif logical_name == "language":
                            state["language"] = "en"  # Default
                        else:
                            state[logical_name] = None
                    
                    return state
                else:
                    logger.error(f"Failed to get contact: {resp.status}")
                    return {"booking_step": "greeting"}
    
    async def update_conversation_state(self, contact_id: str, updates: Dict[str, Any]) -> bool:
        """Update contact custom fields with new state."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/contacts/{contact_id}"
            
            # Map logical names to GHL IDs and prepare array format
            custom_fields = []
            for logical_name, value in updates.items():
                if value is not None and logical_name in self.field_ids:
                    custom_fields.append({
                        "id": self.field_ids[logical_name], 
                        "value": value
                    })
            
            body = {"customFields": custom_fields}
            
            async with session.put(url, headers=self.headers, json=body) as resp:
                if resp.status == 200:
                    return True
                else:
                    error = await resp.text()
                    logger.error(f"Failed to update contact: {resp.status} - {error}")
                    return False
    
    async def send_message(self, phone: str, message: str) -> bool:
        """Send message via GHL (placeholder - implement based on GHL SMS/WhatsApp API)."""
        # In production, this would send via GHL's messaging API
        logger.info(f"Sending to {phone}: {message}")
        return True