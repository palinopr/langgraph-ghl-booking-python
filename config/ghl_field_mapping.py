"""
GHL Custom Field ID Mapping
Maps our logical field names to actual GHL custom field IDs.
"""

# Existing fields in GHL (as of 2025-07-24)
EXISTING_FIELD_IDS = {
    "preferred_day": "D1aD9KUDNm5Lp4Kz8yAD",      # TEXT field
    "preferred_time": "M70lUtadchW4f2pJGDJ5",     # TEXT field
    
    # These fields exist but with different names - we can repurpose them:
    "customer_goal": "r7jFiJBYHiEllsGn7jZC",      # Mapped to existing "goal" field (LARGE_TEXT)
    "customer_budget": "4Qe8P25JRLW0IcZc5iOs",    # Mapped to existing "budget" field (LARGE_TEXT)
    "customer_name": "TjB0I5iNfVwx3zyxZ9sW",      # Mapped to existing "verified_name" field (TEXT)
}

# Fields that need to be created in GHL
FIELDS_TO_CREATE = {
    "booking_step": {
        "name": "Booking Step",
        "type": "SINGLE_OPTIONS",
        "options": ["greeting", "name", "goal", "pain", "budget", "email", "day", "time", "scheduled", "complete"]
    },
    "language": {
        "name": "Language",
        "type": "SINGLE_OPTIONS", 
        "options": ["en", "es"]
    },
    "customer_pain_point": {
        "name": "Customer Pain Point",
        "type": "LARGE_TEXT"
    },
    "customer_email": {
        "name": "Customer Email",
        "type": "TEXT"  # GHL doesn't have EMAIL type for custom fields
    },
    "appointment_id": {
        "name": "Appointment ID",
        "type": "TEXT"
    },
    "conversation_started": {
        "name": "Conversation Started",
        "type": "TEXT"  # Store as ISO string since GHL doesn't have DATETIME type
    },
    "last_interaction": {
        "name": "Last Interaction",
        "type": "TEXT"  # Store as ISO string
    }
}

# Complete mapping (combining existing and to-be-created)
# For now, use the field names as IDs for fields that don't exist yet
CUSTOM_FIELD_IDS = {
    # Existing fields with actual IDs
    "preferred_day": "D1aD9KUDNm5Lp4Kz8yAD",
    "preferred_time": "M70lUtadchW4f2pJGDJ5",
    "customer_goal": "r7jFiJBYHiEllsGn7jZC",
    "customer_budget": "4Qe8P25JRLW0IcZc5iOs",
    "customer_name": "TjB0I5iNfVwx3zyxZ9sW",
    
    # Fields that need to be created (using field names as placeholders)
    "booking_step": "booking_step",  # TODO: Replace with actual ID after creation
    "language": "language",  # TODO: Replace with actual ID after creation
    "customer_pain_point": "customer_pain_point",  # TODO: Replace with actual ID after creation
    "customer_email": "customer_email",  # TODO: Replace with actual ID after creation
    "appointment_id": "appointment_id",  # TODO: Replace with actual ID after creation
    "conversation_started": "conversation_started",  # TODO: Replace with actual ID after creation
    "last_interaction": "last_interaction",  # TODO: Replace with actual ID after creation
}

# Instructions for admin
SETUP_INSTRUCTIONS = """
To complete the setup, please create the following custom fields in GHL:

1. Log into GoHighLevel
2. Go to Settings > Custom Fields (for location sHFG9Rw6BdGh6d6bfMqG)
3. Create these fields:

   - Booking Step (Single Select Options)
     Options: greeting, name, goal, pain, budget, email, day, time, scheduled, complete
   
   - Language (Single Select Options)
     Options: en, es
   
   - Customer Pain Point (Large Text)
   - Customer Email (Text)
   - Appointment ID (Text)
   - Conversation Started (Text)
   - Last Interaction (Text)

4. After creation, update the CUSTOM_FIELD_IDS in this file with the actual IDs
"""