#!/usr/bin/env python3
"""Demo of the conversational flow with real calendar integration"""

print("=== AI Outlet Media Booking System - Calendar Integration Demo ===\n")

print("USER: Hi I need help growing my business")
print("BOT: Hi! I'm María from AI Outlet Media. I'd love to help you grow your business. What's your name?")
print("(Language detected: English)")
print("(Collection step: name)")

print("\nUSER: I'm Sarah Johnson")
print("BOT: Nice to meet you, Sarah Johnson! What specific goals are you looking to achieve with your business?")
print("(Extracted name: Sarah Johnson)")
print("(Collection step: goal)")

print("\nUSER: I want to increase online sales for my boutique")
print("BOT: I understand. What's the biggest challenge you're facing right now with increase online sales for my boutique?")
print("(Extracted goal: increase online sales for my boutique)")
print("(Collection step: pain_point)")

print("\nUSER: My website gets traffic but conversion rate is terrible")
print("BOT: Got it. To ensure we're the right fit, what's your monthly marketing budget? We work with businesses investing $300+ per month.")
print("(Extracted pain point: My website gets traffic but conversion rate is terrible)")
print("(Collection step: budget)")

print("\nUSER: I can invest $500 per month")
print("BOT: Perfect! What's the best email to send you the appointment details?")
print("(Extracted budget: $500)")
print("(Collection step: email)")

print("\nUSER: sarah@boutique.com")
print("BOT: Great! What day works best for your consultation? We have availability Tuesday through Friday.")
print("(Extracted email: sarah@boutique.com)")
print("(Collection step: day)")

print("\nUSER: Tuesday works best for me")
print("(Extracted day: Tuesday)")
print("\n🔄 CALLING GHL API: GET /calendars/default_calendar/free-slots")
print("   Parameters: date=Tuesday, duration=30min")
print("   Response: Found 6 available slots")
print("\nBOT: Excellent! For Tuesday, I have these times available: 9:00 AM, 10:00 AM, 11:00 AM, 2:00 PM, 3:00 PM. Which works best for you?")
print("(Collection step: time)")

print("\nUSER: 10 AM would be perfect")
print("(Extracted time: 10:00 AM)")
print("(Selected slot: {\"start\": \"2024-02-06T10:00:00\", \"end\": \"2024-02-06T10:30:00\", \"display\": \"10:00 AM\"})")
print("(Moving to validation...)")
print("(All fields collected ✓)")
print("(Moving to booking...)")

print("\n🔄 CALLING GHL API: POST /contacts")
print("   Creating/updating contact: Sarah Johnson")
print("   Phone: whatsapp_user")
print("   Email: sarah@boutique.com")
print("   Tags: [\"whatsapp_lead\", \"auto_booked\"]")
print("   Response: Contact created - ID: contact_123456")

print("\n🔄 CALLING GHL API: POST /calendars/events")
print("   Contact ID: contact_123456")
print("   Calendar ID: default_calendar")
print("   Start: Tuesday, February 6 at 10:00 AM")
print("   End: Tuesday, February 6 at 10:30 AM")
print("   Title: AI Outlet Media Consultation - Sarah Johnson")
print("   Notes: Goal: increase online sales for my boutique")
print("         Budget: $500")
print("         Pain Point: My website gets traffic but conversion rate is terrible")
print("   Response: Appointment created successfully!")

print("\nBOT: Perfect! Your consultation is confirmed for Tuesday, February 6 at 10:00 AM. I'll send the details to sarah@boutique.com. Looking forward to helping you increase online sales for my boutique!")

print("\n=== Key Features Demonstrated ===")
print("✓ Real-time calendar availability check via GHL API")
print("✓ Dynamic time slot presentation based on selected day")
print("✓ User selects from actual available times")
print("✓ Contact creation with all collected information")
print("✓ Appointment booking with detailed notes")
print("✓ Complete integration with GoHighLevel calendar system")