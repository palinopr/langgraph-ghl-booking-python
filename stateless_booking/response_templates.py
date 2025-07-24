"""
Response templates for each conversation step.
Simple dictionary lookup - no complex logic.
"""

TEMPLATES = {
    "en": {
        "greeting": "Hi! I'm Maria from AI Outlet Media. I'd love to help you grow your business. What's your name?",
        "ask_goal": "Nice to meet you {name}! What specific goals are you looking to achieve for your business?",
        "ask_goal_again": "Could you tell me more about what you'd like to achieve for your business?",
        "ask_pain": "I understand. What's the biggest challenge you're facing right now in reaching those goals?",
        "ask_pain_again": "What specific challenges are preventing you from achieving your goals?",
        "ask_budget": "What's your monthly marketing budget to invest in solving this challenge?",
        "ask_budget_again": "Could you share your approximate monthly marketing budget? (Please include a number)",
        "budget_too_low": "I appreciate your interest! We work with businesses investing at least $300/month in marketing. Feel free to reach out when you're ready to invest in growth.",
        "ask_email": "Perfect! What's the best email to send you the appointment details?",
        "ask_email_again": "Please provide a valid email address so I can send you the appointment details.",
        "ask_day": "What day works best for you for a quick call? We have availability Tuesday through Friday.",
        "ask_day_again": "Please choose a day between Tuesday and Friday that works best for you.",
        "ask_time": "Great! I have these times available on {day}: {times}. Which works best for you?",
        "ask_time_again": "Please choose one of the available time slots mentioned above.",
        "appointment_confirmed": "Perfect! Your appointment is confirmed for {day} at {time}. I've sent the details to {email}. Looking forward to speaking with you!",
        "conversation_complete": "Thank you! If you need anything else, feel free to reach out.",
        "ask_name_again": "I didn't catch your name. What should I call you?"
    },
    "es": {
        "greeting": "¡Hola! Soy María de AI Outlet Media. Me encantaría ayudarte a hacer crecer tu negocio. ¿Cuál es tu nombre?",
        "ask_goal": "¡Mucho gusto {name}! ¿Qué objetivos específicos quieres lograr para tu negocio?",
        "ask_goal_again": "¿Podrías contarme más sobre lo que te gustaría lograr para tu negocio?",
        "ask_pain": "Entiendo. ¿Cuál es el mayor desafío que enfrentas actualmente para alcanzar esos objetivos?",
        "ask_pain_again": "¿Qué desafíos específicos te impiden alcanzar tus objetivos?",
        "ask_budget": "¿Cuál es tu presupuesto mensual de marketing para invertir en resolver este desafío?",
        "ask_budget_again": "¿Podrías compartir tu presupuesto mensual aproximado de marketing? (Por favor incluye un número)",
        "budget_too_low": "¡Aprecio tu interés! Trabajamos con negocios que invierten al menos $300/mes en marketing. No dudes en contactarnos cuando estés listo para invertir en crecimiento.",
        "ask_email": "¡Perfecto! ¿Cuál es el mejor correo electrónico para enviarte los detalles de la cita?",
        "ask_email_again": "Por favor proporciona un correo electrónico válido para enviarte los detalles de la cita.",
        "ask_day": "¿Qué día te funciona mejor para una llamada rápida? Tenemos disponibilidad de martes a viernes.",
        "ask_day_again": "Por favor elige un día entre martes y viernes que te funcione mejor.",
        "ask_time": "¡Excelente! Tengo estos horarios disponibles el {day}: {times}. ¿Cuál te funciona mejor?",
        "ask_time_again": "Por favor elige uno de los horarios disponibles mencionados arriba.",
        "appointment_confirmed": "¡Perfecto! Tu cita está confirmada para el {day} a las {time}. He enviado los detalles a {email}. ¡Espero hablar contigo pronto!",
        "conversation_complete": "¡Gracias! Si necesitas algo más, no dudes en contactarnos.",
        "ask_name_again": "No entendí tu nombre. ¿Cómo te llamas?"
    }
}


def get_template(template_name: str, language: str = "en", **kwargs) -> str:
    """
    Get response template and format with provided values.
    
    Args:
        template_name: Name of the template
        language: Language code (en/es)
        **kwargs: Values to format into template
        
    Returns:
        Formatted message string
    """
    template = TEMPLATES.get(language, TEMPLATES["en"]).get(template_name, "")
    
    if kwargs:
        return template.format(**kwargs)
    return template