"""Workflow nodes for the booking agent."""
import re
from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langsmith import traceable
import yaml
import os

from booking_agent.utils.state import BookingState
from booking_agent.utils.tools import book_appointment, GHLClient


async def send_ghl_message(state: BookingState, message: str) -> None:
    """Send message via GHL API if we have contact information."""
    try:
        # Get contact_id if available
        contact_id = state.get("contact_id")
        if not contact_id:
            # Try to create contact if we have phone
            phone = state.get("thread_id", "").replace("whatsapp:", "")
            if phone and phone != "default":
                ghl_client = GHLClient()
                # Create minimal contact to get ID
                contact = await ghl_client.create_contact(
                    name=state.get("customer_name", "WhatsApp User"),
                    phone=phone,
                    tags=["whatsapp_conversation"]
                )
                contact_id = contact.get("id")
        
        # Send message if we have contact_id
        if contact_id:
            ghl_client = GHLClient()
            await ghl_client.send_message(
                contact_id=contact_id,
                message=message,
                conversation_id=state.get("conversation_id")
            )
    except Exception as e:
        # Log error but don't fail - webhook response is backup
        print(f"Error sending GHL message: {str(e)}")


# Load business configuration
def load_config() -> Dict[str, Any]:
    """Load business configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), "../../config/config.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    # Default config if file doesn't exist
    return {
        "business": {
            "name": "FitLife Coaching",
            "minimum_budget": 1000,
            "timezone": "PST"
        }
    }


@traceable(name="triage_node", run_type="chain")
async def triage_node(state: BookingState) -> Dict[str, Any]:
    """Triage incoming messages to filter spam and determine if booking intent exists.
    
    This node:
    1. Checks for spam keywords
    2. Determines if the message shows booking intent
    3. Routes to collect or marks as spam
    """
    messages = state.get("messages", [])
    if not messages:
        return {
            "is_spam": True,
            "current_step": "complete",
            "messages": []
        }
    
    last_message = messages[-1].content.lower()
    
    # Spam detection
    spam_keywords = ["crypto", "investment", "viagra", "casino", "lottery", "prize"]
    if any(keyword in last_message for keyword in spam_keywords):
        response_message = "Sorry, I can only help with fitness coaching appointments."
        await send_ghl_message(state, response_message)
        return {
            "is_spam": True,
            "current_step": "complete",
            "messages": messages + [AIMessage(content=response_message)]
        }
    
    # Check for booking intent
    booking_keywords = ["appointment", "book", "schedule", "meet", "consultation", "fitness", "training", "coach"]
    has_booking_intent = any(keyword in last_message for keyword in booking_keywords)
    
    if has_booking_intent or len(messages) == 1:  # First message gets benefit of doubt
        return {
            "messages": messages,
            "is_spam": False,
            "current_step": "collect"
        }
    else:
        response_message = "I'm here to help you book a fitness consultation. Would you like to schedule an appointment?"
        await send_ghl_message(state, response_message)
        return {
            "is_spam": True,
            "current_step": "complete",
            "messages": messages + [AIMessage(content=response_message)]
        }


def detect_language(text: str) -> str:
    """Detect if text is in Spanish or English."""
    spanish_indicators = [
        'hola', 'necesito', 'ayuda', 'quiero', 'puedo', 'gracias',
        'por favor', 'cómo', 'qué', 'cuál', 'dónde', 'cuándo',
        'á', 'é', 'í', 'ó', 'ú', 'ñ'
    ]
    
    text_lower = text.lower()
    spanish_count = sum(1 for indicator in spanish_indicators if indicator in text_lower)
    
    return "es" if spanish_count >= 2 else "en"


def get_response_template(step: str, language: str) -> str:
    """Get conversational response template for current step."""
    templates = {
        "en": {
            "greeting": "Hi! I'm María from AI Outlet Media. I'd love to help you grow your business. What's your name?",
            "goal": "Nice to meet you, {name}! What specific goals are you looking to achieve with your business?",
            "pain_point": "I understand. What's the biggest challenge you're facing right now with {goal}?",
            "budget": "Got it. To ensure we're the right fit, what's your monthly marketing budget? We work with businesses investing $300+ per month.",
            "budget_too_low": "I appreciate your honesty! Our programs start at $300/month to ensure we can deliver real results. Would you be open to adjusting your budget in the future?",
            "email": "Perfect! What's the best email to send you the appointment details?",
            "day": "Great! What day works best for your consultation? We have availability Tuesday through Friday.",
            "time_selection": "Excellent! For {day}, I have these times available: {times}. Which works best for you?",
            "confirmation": "Perfect! Your consultation is confirmed for {day} at {time}. I'll send the details to {email}. Looking forward to helping you {goal}!"
        },
        "es": {
            "greeting": "¡Hola! Soy María de AI Outlet Media. Me encantaría ayudarte a crecer tu negocio. ¿Cuál es tu nombre?",
            "goal": "¡Mucho gusto, {name}! ¿Qué objetivos específicos quieres lograr con tu negocio?",
            "pain_point": "Entiendo. ¿Cuál es el mayor desafío que enfrentas ahora mismo con {goal}?",
            "budget": "Perfecto. Para asegurarnos de que somos la opción correcta, ¿cuál es tu presupuesto mensual de marketing? Trabajamos con negocios que invierten $300+ al mes.",
            "budget_too_low": "¡Aprecio tu honestidad! Nuestros programas comienzan en $300/mes para asegurar resultados reales. ¿Estarías dispuesto a ajustar tu presupuesto en el futuro?",
            "email": "¡Excelente! ¿Cuál es el mejor correo para enviarte los detalles de la cita?",
            "day": "¡Genial! ¿Qué día te funciona mejor para tu consulta? Tenemos disponibilidad de martes a viernes.",
            "time_selection": "¡Perfecto! Para el {day}, tengo estos horarios disponibles: {times}. ¿Cuál prefieres?",
            "confirmation": "¡Listo! Tu consulta está confirmada para el {day} a las {time}. Te enviaré los detalles a {email}. ¡Esperamos ayudarte con {goal}!"
        }
    }
    
    return templates.get(language, templates["en"]).get(step, "")


@traceable(name="collect_node", run_type="chain")
async def collect_node(state: BookingState) -> Dict[str, Any]:
    """Collect customer information through natural conversation.
    
    This node implements a step-by-step conversational flow:
    1. Detect language (Spanish/English)
    2. Collect: Name → Goal → Pain Point → Budget → Email → Day
    3. Use natural, conversational responses
    4. Extract information intelligently from messages
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": messages, "current_step": "collect"}
    
    # Get current collection step or start from beginning
    collection_step = state.get("collection_step", "greeting")
    language = state.get("language")
    
    # Detect language from first human message if not set
    if not language and messages:
        first_human_msg = next((m for m in messages if hasattr(m, 'content') and m.type == "human"), None)
        if first_human_msg:
            language = detect_language(first_human_msg.content)
    
    language = language or "en"
    
    # Get current values
    customer_name = state.get("customer_name")
    customer_goal = state.get("customer_goal")
    customer_pain_point = state.get("customer_pain_point")
    customer_budget = state.get("customer_budget", 0)
    customer_email = state.get("customer_email")
    preferred_day = state.get("preferred_day")
    preferred_time = state.get("preferred_time")
    available_slots = state.get("available_slots", [])
    
    # Initialize LLM for extraction
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.3)
    
    # Get last human message
    last_human_msg = None
    for msg in reversed(messages):
        if hasattr(msg, 'content') and msg.type == "human":
            last_human_msg = msg.content
            break
    
    if not last_human_msg:
        # First interaction - send greeting
        greeting = get_response_template("greeting", language)
        await send_ghl_message(state, greeting)
        return {
            "messages": messages + [AIMessage(content=greeting)],
            "collection_step": "name",
            "language": language,
            "current_step": "collect"
        }
    
    # Extract information based on current step
    if collection_step == "name" and not customer_name:
        # Extract name
        extraction_prompt = f"""Extract the person's name from this message: "{last_human_msg}"
        Return ONLY the name or "none" if no name found.
        Examples: "John Smith", "María", "none" """
        
        response = await llm.ainvoke(extraction_prompt)
        extracted_name = response.content.strip()
        if extracted_name and extracted_name.lower() != "none":
            customer_name = extracted_name
            next_step = "goal"
            template = get_response_template("goal", language)
            response_text = template.format(name=customer_name)
        else:
            # Ask again for name
            response_text = get_response_template("greeting", language)
            next_step = "name"
    
    elif collection_step == "goal" and customer_name and not customer_goal:
        # Extract goal
        extraction_prompt = f"""Extract the business goal from this message: "{last_human_msg}"
        Return a brief description of their goal (max 50 chars) or "none" if unclear.
        Examples: "increase sales", "get more clients", "grow online presence" """
        
        response = await llm.ainvoke(extraction_prompt)
        extracted_goal = response.content.strip()
        if extracted_goal and extracted_goal.lower() != "none":
            customer_goal = extracted_goal
            next_step = "pain_point"
            template = get_response_template("pain_point", language)
            response_text = template.format(goal=customer_goal)
        else:
            # Ask again for goal
            template = get_response_template("goal", language)
            response_text = template.format(name=customer_name)
            next_step = "goal"
    
    elif collection_step == "pain_point" and customer_goal and not customer_pain_point:
        # Extract pain point
        customer_pain_point = last_human_msg[:200]  # Store their exact words
        next_step = "budget"
        response_text = get_response_template("budget", language)
    
    elif collection_step == "budget" and not customer_budget:
        # Extract budget
        extraction_prompt = f"""Extract the monthly budget amount from: "{last_human_msg}"
        Return ONLY the numeric amount (no currency symbols) or "0" if not found.
        Examples: "500", "1000", "0" """
        
        response = await llm.ainvoke(extraction_prompt)
        try:
            extracted_budget = float(response.content.strip())
            customer_budget = extracted_budget
            
            if customer_budget >= 300:
                next_step = "email"
                response_text = get_response_template("email", language)
            else:
                # Budget too low
                next_step = "budget"  # Stay on budget step
                response_text = get_response_template("budget_too_low", language)
                # Don't save the low budget
                customer_budget = 0
        except:
            # Ask again for budget
            response_text = get_response_template("budget", language)
            next_step = "budget"
    
    elif collection_step == "email" and customer_budget >= 300 and not customer_email:
        # Extract email
        extraction_prompt = f"""Extract the email address from: "{last_human_msg}"
        Return ONLY the email or "none" if not found.
        Examples: "john@example.com", "none" """
        
        response = await llm.ainvoke(extraction_prompt)
        extracted_email = response.content.strip()
        if extracted_email and extracted_email.lower() != "none" and "@" in extracted_email:
            customer_email = extracted_email
            next_step = "day"
            response_text = get_response_template("day", language)
        else:
            # Ask again for email
            response_text = get_response_template("email", language)
            next_step = "email"
    
    elif collection_step == "day" and customer_email and not preferred_day:
        # Extract preferred day
        extraction_prompt = f"""Extract the day of the week from: "{last_human_msg}"
        Return one of: Tuesday, Wednesday, Thursday, Friday or "none"
        Examples: "Tuesday", "Friday", "none" """
        
        response = await llm.ainvoke(extraction_prompt)
        extracted_day = response.content.strip()
        if extracted_day in ["Tuesday", "Wednesday", "Thursday", "Friday"]:
            preferred_day = extracted_day
            
            # Fetch available times for this day
            ghl_client = GHLClient()
            calendar_id = os.getenv("GHL_CALENDAR_ID", "default_calendar")
            available_slots = await ghl_client.get_available_slots_for_day(
                calendar_id=calendar_id,
                day_name=preferred_day
            )
            
            # Format times for display
            if available_slots:
                times_display = ", ".join([slot["display"] for slot in available_slots[:5]])  # Show max 5 slots
                template = get_response_template("time_selection", language)
                response_text = template.format(day=preferred_day, times=times_display)
                next_step = "time"
            else:
                # No slots available for this day
                response_text = f"I don't have any slots available on {preferred_day}. Could you choose another day between Tuesday and Friday?"
                if language == "es":
                    response_text = f"No tengo horarios disponibles el {preferred_day}. ¿Podrías elegir otro día entre martes y viernes?"
                next_step = "day"
                preferred_day = None  # Reset day selection
            
            await send_ghl_message(state, response_text)
            return {
                "messages": messages + [AIMessage(content=response_text)],
                "customer_name": customer_name,
                "customer_goal": customer_goal,
                "customer_pain_point": customer_pain_point,
                "customer_budget": customer_budget,
                "customer_email": customer_email,
                "preferred_day": preferred_day,
                "available_slots": available_slots,
                "collection_step": next_step,
                "language": language,
                "current_step": "collect"
            }
        else:
            # Ask again for day
            response_text = get_response_template("day", language)
            next_step = "day"
    
    elif collection_step == "time" and preferred_day and available_slots and not preferred_time:
        # Extract time selection
        extraction_prompt = f"""Extract the time from: "{last_human_msg}"
        Available times are: {', '.join([slot['display'] for slot in available_slots])}
        Return the exact time if mentioned (e.g., "10:00 AM") or "none" if not found."""
        
        response = await llm.ainvoke(extraction_prompt)
        extracted_time = response.content.strip()
        
        # Find matching slot
        selected_slot = None
        for slot in available_slots:
            if slot["display"].lower() in extracted_time.lower() or extracted_time.lower() in slot["display"].lower():
                selected_slot = slot
                break
        
        if selected_slot:
            preferred_time = selected_slot["display"]
            # All info collected, move to validation
            return {
                "messages": messages,
                "customer_name": customer_name,
                "customer_goal": customer_goal,
                "customer_pain_point": customer_pain_point,
                "customer_budget": customer_budget,
                "customer_email": customer_email,
                "preferred_day": preferred_day,
                "preferred_time": preferred_time,
                "available_slots": available_slots,
                "selected_slot": selected_slot,
                "language": language,
                "current_step": "validate"
            }
        else:
            # Ask again for time
            times_display = ", ".join([slot["display"] for slot in available_slots[:5]])
            template = get_response_template("time_selection", language)
            response_text = template.format(day=preferred_day, times=times_display)
            next_step = "time"
    
    else:
        # All info collected or in unexpected state
        if all([customer_name, customer_goal, customer_pain_point, 
                customer_budget >= 300, customer_email, preferred_day, preferred_time]):
            return {
                "messages": messages,
                "customer_name": customer_name,
                "customer_goal": customer_goal,
                "customer_pain_point": customer_pain_point,
                "customer_budget": customer_budget,
                "customer_email": customer_email,
                "preferred_day": preferred_day,
                "preferred_time": preferred_time,
                "available_slots": available_slots,
                "language": language,
                "current_step": "validate"
            }
        else:
            # Determine what's missing and ask for it
            if not customer_name:
                next_step = "name"
                response_text = get_response_template("greeting", language)
            elif not customer_goal:
                next_step = "goal"
                template = get_response_template("goal", language)
                response_text = template.format(name=customer_name)
            elif not customer_pain_point:
                next_step = "pain_point"
                template = get_response_template("pain_point", language)
                response_text = template.format(goal=customer_goal)
            elif customer_budget < 300:
                next_step = "budget"
                response_text = get_response_template("budget", language)
            elif not customer_email:
                next_step = "email"
                response_text = get_response_template("email", language)
            elif not preferred_day:
                next_step = "day"
                response_text = get_response_template("day", language)
            else:
                next_step = "time"
                # Re-fetch available times if needed
                if not available_slots:
                    ghl_client = GHLClient()
                    calendar_id = os.getenv("GHL_CALENDAR_ID", "default_calendar")
                    available_slots = await ghl_client.get_available_slots_for_day(
                        calendar_id=calendar_id,
                        day_name=preferred_day
                    )
                times_display = ", ".join([slot["display"] for slot in available_slots[:5]])
                template = get_response_template("time_selection", language)
                response_text = template.format(day=preferred_day, times=times_display)
    
    # Return updated state with response
    await send_ghl_message(state, response_text)
    return {
        "messages": messages + [AIMessage(content=response_text)],
        "customer_name": customer_name,
        "customer_goal": customer_goal,
        "customer_pain_point": customer_pain_point,
        "customer_budget": customer_budget,
        "customer_email": customer_email,
        "preferred_day": preferred_day,
        "preferred_time": preferred_time,
        "available_slots": available_slots,
        "collection_step": next_step,
        "language": language,
        "current_step": "collect"
    }


@traceable(name="validate_node", run_type="chain")
async def validate_node(state: BookingState) -> Dict[str, Any]:
    """Validate collected information against business rules.
    
    This node:
    1. Checks if budget meets minimum requirement
    2. Validates all required fields are present
    3. Routes to booking or back to collect with errors
    """
    config = load_config()
    minimum_budget = config["business"]["minimum_budget"]
    
    customer_name = state.get("customer_name")
    customer_goal = state.get("customer_goal")
    customer_pain_point = state.get("customer_pain_point")
    customer_budget = state.get("customer_budget", 0)
    customer_email = state.get("customer_email")
    preferred_day = state.get("preferred_day")
    preferred_time = state.get("preferred_time")
    available_slots = state.get("available_slots", [])
    messages = state.get("messages", [])
    language = state.get("language", "en")
    
    validation_errors = []
    
    # Validate required fields
    if not customer_name:
        validation_errors.append("Name is required")
    if not customer_goal:
        validation_errors.append("Business goal is required")
    if not customer_pain_point:
        validation_errors.append("Pain point is required")
    if not customer_budget:
        validation_errors.append("Budget is required")
    if not customer_email:
        validation_errors.append("Email is required")
    if not preferred_day:
        validation_errors.append("Preferred day is required")
    if not preferred_time:
        validation_errors.append("Preferred time is required")
    
    # Validate budget minimum
    if customer_budget and customer_budget < minimum_budget:
        validation_errors.append(f"Our programs start at ${minimum_budget}/month")
    
    if validation_errors:
        # Send validation errors and go back to collect
        error_message = f"I notice a few things: {', '.join(validation_errors)}. Could you help me with this information?"
        await send_ghl_message(state, error_message)
        return {
            "messages": messages + [AIMessage(content=error_message)],
            "validation_errors": validation_errors,
            "current_step": "collect"
        }
    else:
        # Validation passed, proceed to booking
        return {
            "messages": messages,
            "customer_name": customer_name,
            "customer_goal": customer_goal,
            "customer_pain_point": customer_pain_point,
            "customer_budget": customer_budget,
            "customer_email": customer_email,
            "preferred_day": preferred_day,
            "preferred_time": preferred_time,
            "available_slots": available_slots,
            "language": language,
            "validation_errors": [],
            "current_step": "book"
        }


@traceable(name="booking_node", run_type="chain")
async def booking_node(state: BookingState) -> Dict[str, Any]:
    """Book the appointment in GoHighLevel.
    
    This node:
    1. Creates/updates contact in GHL
    2. Finds available appointment slot
    3. Books the appointment
    4. Returns confirmation message
    """
    customer_name = state["customer_name"]
    customer_goal = state["customer_goal"]
    customer_pain_point = state["customer_pain_point"]
    customer_budget = state["customer_budget"]
    customer_email = state["customer_email"]
    preferred_day = state["preferred_day"]
    preferred_time = state["preferred_time"]
    language = state.get("language", "en")
    messages = state.get("messages", [])
    available_slots = state.get("available_slots", [])
    selected_slot = state.get("selected_slot")
    
    # Extract phone number from thread_id or use placeholder
    phone = state.get("thread_id", "whatsapp_user")
    
    try:
        # Book the appointment using our GHL tools
        result = await book_appointment(
            customer_name=customer_name,
            customer_phone=phone,
            customer_goal=customer_goal,
            customer_budget=customer_budget,
            customer_email=customer_email,
            customer_pain_point=customer_pain_point,
            selected_slot=selected_slot
        )
        
        if result["success"]:
            confirmation_message = result["message"]
            # Translate confirmation if Spanish
            if language == "es":
                template = get_response_template("confirmation", language)
                appointment_time = selected_slot["start"] if selected_slot else datetime.now()
                confirmation_message = template.format(
                    day=preferred_day,
                    time=preferred_time,
                    email=customer_email,
                    goal=customer_goal
                )
            
            # Store contact_id for future messages
            contact_id = result.get("contact", {}).get("id")
            
            await send_ghl_message(state, confirmation_message)
            return {
                "messages": messages + [AIMessage(content=confirmation_message)],
                "booking_result": result,
                "contact_id": contact_id,
                "current_step": "complete"
            }
        else:
            error_message = f"I'm having trouble booking your appointment: {result.get('error', 'Unknown error')}. Let me try again or connect you with our team."
            await send_ghl_message(state, error_message)
            return {
                "messages": messages + [AIMessage(content=error_message)],
                "booking_result": result,
                "current_step": "complete"
            }
    except Exception as e:
        # Handle any booking errors
        error_message = "I encountered an issue while booking your appointment. Our team will reach out to you directly to complete the booking."
        await send_ghl_message(state, error_message)
        return {
            "messages": messages + [AIMessage(content=error_message)],
            "booking_result": {"success": False, "error": str(e)},
            "current_step": "complete"
        }