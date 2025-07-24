#!/usr/bin/env python3
"""Test end-to-end webhook flow with real GHL booking."""

import requests
import json
import time
from datetime import datetime

# Webhook configuration
WEBHOOK_URL = "http://localhost:4000/webhook"
WEBHOOK_SECRET = "your_webhook_secret_here"  # From .env

def send_whatsapp_message(message: str, conversation_id: str = None):
    """Send a simulated WhatsApp message to the webhook."""
    conversation_id = conversation_id or f"test_convo_{int(time.time())}"
    
    payload = {
        "message": message,
        "phone": "+1234567890",
        "conversationId": conversation_id,
        "name": None,  # Will be extracted from conversation
        "email": None,  # Will be extracted from conversation
        "messageType": "SMS",
        "direction": "IN"
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-webhook-secret": WEBHOOK_SECRET
    }
    
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    
    print(f"\n📱 USER: {message}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"🤖 BOT: {data.get('message', 'No response')}")
        return conversation_id, data
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return conversation_id, None


def test_full_booking_flow():
    """Test complete booking flow from greeting to appointment."""
    print("=== TESTING END-TO-END WEBHOOK BOOKING FLOW ===")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Start conversation
    conversation_id = None
    
    # 1. Initial greeting (Spanish)
    conversation_id, _ = send_whatsapp_message("Hola, necesito ayuda con marketing", conversation_id)
    time.sleep(1)
    
    # 2. Provide name
    conversation_id, _ = send_whatsapp_message("Soy Maria Rodriguez", conversation_id)
    time.sleep(1)
    
    # 3. Provide goal
    conversation_id, _ = send_whatsapp_message("Quiero más ventas online para mi tienda", conversation_id)
    time.sleep(1)
    
    # 4. Provide pain point
    conversation_id, _ = send_whatsapp_message("Mi sitio web no convierte visitantes en clientes", conversation_id)
    time.sleep(1)
    
    # 5. Provide budget
    conversation_id, _ = send_whatsapp_message("Puedo invertir $600 al mes", conversation_id)
    time.sleep(1)
    
    # 6. Provide email
    conversation_id, _ = send_whatsapp_message("maria@mitienda.com", conversation_id)
    time.sleep(1)
    
    # 7. Select day
    conversation_id, _ = send_whatsapp_message("El viernes me funciona bien", conversation_id)
    time.sleep(2)  # Wait for calendar check
    
    # 8. Select time
    conversation_id, response = send_whatsapp_message("10 AM está perfecto", conversation_id)
    time.sleep(1)
    
    print("\n" + "=" * 50)
    print("🎯 BOOKING FLOW COMPLETE!")
    print("=" * 50)
    
    if response and "confirmation" in response.get("message", "").lower():
        print("✅ Appointment successfully booked!")
    else:
        print("⚠️  Check if appointment was created in GHL")
    
    print("\n📋 Summary:")
    print(f"   - Conversation ID: {conversation_id}")
    print(f"   - Language: Spanish (detected)")
    print(f"   - Name: Maria Rodriguez")
    print(f"   - Email: maria@mitienda.com")
    print(f"   - Budget: $600/month")
    print(f"   - Day: Friday")
    print(f"   - Time: 10:00 AM")
    
    print("\n🔍 Please verify in GHL dashboard:")
    print("   1. New contact 'Maria Rodriguez' created")
    print("   2. Tags applied: whatsapp_lead, auto_booked")
    print("   3. Appointment shows on Friday at 10 AM")
    print("   4. Notes include goal, pain point, and budget")


if __name__ == "__main__":
    test_full_booking_flow()