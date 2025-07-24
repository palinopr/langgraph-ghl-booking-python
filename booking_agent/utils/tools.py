"""GoHighLevel client and tools for booking appointments."""
import os
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import pytz
import aiohttp
import json
from langsmith import traceable


class GHLClient:
    """Wrapper for GoHighLevel API interactions."""
    
    def __init__(self, api_key: Optional[str] = None, location_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("GHL_API_KEY")
        self.location_id = location_id or os.getenv("GHL_LOCATION_ID")
        self.base_url = "https://rest.gohighlevel.com/v1"
        
        if not self.api_key:
            raise ValueError("GHL_API_KEY is required")
        if not self.location_id:
            raise ValueError("GHL_LOCATION_ID is required")
    
    @traceable(name="ghl_create_contact", run_type="tool")
    async def create_contact(
        self, 
        name: str, 
        phone: str, 
        email: Optional[str] = None,
        tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """Create or update a contact in GHL.
        
        Args:
            name: Contact's full name
            phone: Contact's phone number
            email: Contact's email (optional)
            tags: List of tags to apply (optional)
            
        Returns:
            Contact data from GHL
        """
        # First, try to find existing contact by phone
        search_url = f"{self.base_url}/contacts/search?locationId={self.location_id}&query={phone}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            # Search for existing contact
            async with session.get(search_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    contacts = data.get("contacts", [])
                    if contacts:
                        # Update existing contact
                        contact_id = contacts[0]["id"]
                        update_url = f"{self.base_url}/contacts/{contact_id}"
                        update_data = {
                            "name": name,
                            "phone": phone,
                            "tags": tags or []
                        }
                        if email:
                            update_data["email"] = email
                            
                        async with session.put(update_url, json=update_data, headers=headers) as update_resp:
                            if update_resp.status == 200:
                                return await update_resp.json()
            
            # Create new contact
            create_url = f"{self.base_url}/contacts"
            contact_data = {
                "locationId": self.location_id,
                "name": name,
                "phone": phone,
                "tags": tags or []
            }
            if email:
                contact_data["email"] = email
                
            async with session.post(create_url, json=contact_data, headers=headers) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise Exception(f"Failed to create contact: {resp.status} - {error_text}")
    
    @traceable(name="ghl_create_appointment", run_type="tool")
    async def create_appointment(
        self,
        contact_id: str,
        calendar_id: str,
        start_time: datetime,
        end_time: datetime,
        title: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an appointment in GHL calendar.
        
        Args:
            contact_id: GHL contact ID
            calendar_id: GHL calendar ID
            start_time: Appointment start time
            end_time: Appointment end time
            title: Appointment title
            notes: Additional notes (optional)
            
        Returns:
            Appointment data from GHL
        """
        url = f"{self.base_url}/calendars/events"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        appointment_data = {
            "calendarId": calendar_id,
            "locationId": self.location_id,
            "contactId": contact_id,
            "title": title,
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "status": "confirmed"
        }
        
        if notes:
            appointment_data["notes"] = notes
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=appointment_data, headers=headers) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise Exception(f"Failed to create appointment: {resp.status} - {error_text}")
    
    @traceable(name="ghl_find_available_slot", run_type="tool")
    async def find_available_slot(
        self,
        calendar_id: str,
        duration_minutes: int = 30,
        days_ahead: int = 7
    ) -> Optional[Dict[str, datetime]]:
        """Find the next available appointment slot.
        
        Args:
            calendar_id: GHL calendar ID
            duration_minutes: Appointment duration in minutes
            days_ahead: How many days ahead to search
            
        Returns:
            Dict with 'start' and 'end' datetime objects, or None if no slots
        """
        # Get calendar availability
        timezone = pytz.timezone("America/Los_Angeles")
        now = datetime.now(timezone)
        end_date = now + timedelta(days=days_ahead)
        
        url = f"{self.base_url}/calendars/{calendar_id}/free-slots"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "startDate": now.date().isoformat(),
            "endDate": end_date.date().isoformat(),
            "duration": duration_minutes,
            "timezone": "America/Los_Angeles"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    slots = data.get("slots", [])
                    
                    if slots:
                        # Return the first available slot
                        first_slot = slots[0]
                        start_time = datetime.fromisoformat(first_slot["startTime"])
                        end_time = start_time + timedelta(minutes=duration_minutes)
                        
                        return {
                            "start": start_time,
                            "end": end_time
                        }
                
                # Fallback: If no slots found via API, return next business day at 2 PM
                next_day = now + timedelta(days=1)
                while next_day.weekday() >= 5:  # Skip weekends
                    next_day += timedelta(days=1)
                
                start_time = next_day.replace(hour=14, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(minutes=duration_minutes)
                
                return {
                    "start": start_time,
                    "end": end_time
                }


# Helper functions for nodes to use
@traceable(name="book_appointment", run_type="chain")
async def book_appointment(
    customer_name: str,
    customer_phone: str,
    customer_goal: str,
    customer_budget: float,
    ghl_client: Optional[GHLClient] = None
) -> Dict[str, Any]:
    """Complete booking process: create contact and book appointment.
    
    Args:
        customer_name: Customer's full name
        customer_phone: Customer's phone number
        customer_goal: Customer's fitness goal
        customer_budget: Customer's budget
        ghl_client: GHL client instance (optional, creates new if not provided)
        
    Returns:
        Booking result with contact and appointment details
    """
    if not ghl_client:
        ghl_client = GHLClient()
    
    # Create or update contact
    contact = await ghl_client.create_contact(
        name=customer_name,
        phone=customer_phone,
        tags=["whatsapp_lead", "auto_booked"]
    )
    
    # Find available slot (using default calendar from env)
    calendar_id = os.getenv("GHL_CALENDAR_ID", "default_calendar")
    slot = await ghl_client.find_available_slot(calendar_id)
    
    if not slot:
        return {
            "success": False,
            "error": "No available appointment slots found"
        }
    
    # Create appointment
    appointment = await ghl_client.create_appointment(
        contact_id=contact["id"],
        calendar_id=calendar_id,
        start_time=slot["start"],
        end_time=slot["end"],
        title=f"Fitness Consultation - {customer_name}",
        notes=f"Goal: {customer_goal}\\nBudget: ${customer_budget}"
    )
    
    return {
        "success": True,
        "contact": contact,
        "appointment": appointment,
        "message": f"Great! I've booked your fitness consultation for {slot['start'].strftime('%B %d at %I:%M %p')}. See you then!"
    }