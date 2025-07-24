#!/usr/bin/env python3
"""Demo of the conversational flow"""

# Example conversation flow demonstration
print("=== AI Outlet Media Booking System - Conversational Demo ===\n")

print("USER: Hola necesito ayuda")
print("BOT: ¡Hola! Soy María de AI Outlet Media. Me encantaría ayudarte a crecer tu negocio. ¿Cuál es tu nombre?")
print("(Language detected: Spanish)")
print("(Collection step: name)")

print("\nUSER: Soy Carlos")
print("BOT: ¡Mucho gusto, Carlos! ¿Qué objetivos específicos quieres lograr con tu negocio?")
print("(Extracted name: Carlos)")
print("(Collection step: goal)")

print("\nUSER: Quiero más clientes para mi restaurante")
print("BOT: Entiendo. ¿Cuál es el mayor desafío que enfrentas ahora mismo con más clientes para mi restaurante?")
print("(Extracted goal: más clientes para mi restaurante)")
print("(Collection step: pain_point)")

print("\nUSER: La gente no conoce mi restaurante, está en una zona nueva")
print("BOT: Perfecto. Para asegurarnos de que somos la opción correcta, ¿cuál es tu presupuesto mensual de marketing? Trabajamos con negocios que invierten $300+ al mes.")
print("(Extracted pain point: La gente no conoce mi restaurante, está en una zona nueva)")
print("(Collection step: budget)")

print("\nUSER: Puedo invertir $500 al mes")
print("BOT: ¡Excelente! ¿Cuál es el mejor correo para enviarte los detalles de la cita?")
print("(Extracted budget: $500)")
print("(Collection step: email)")

print("\nUSER: carlos@mirestaurante.com")
print("BOT: ¡Genial! ¿Qué día te funciona mejor para tu consulta? Tenemos disponibilidad de martes a viernes.")
print("(Extracted email: carlos@mirestaurante.com)")
print("(Collection step: day)")

print("\nUSER: El martes me viene bien")
print("(Extracted day: Tuesday)")
print("(Moving to validation...)")
print("(All fields collected ✓)")
print("(Moving to booking...)")

print("\n=== English Conversation Example ===\n")

print("USER: Hi I need help")
print("BOT: Hi! I'm María from AI Outlet Media. I'd love to help you grow your business. What's your name?")
print("(Language detected: English)")

print("\nUSER: I'm Sarah")
print("BOT: Nice to meet you, Sarah! What specific goals are you looking to achieve with your business?")

print("\nUSER: I want to increase online sales")
print("BOT: I understand. What's the biggest challenge you're facing right now with increase online sales?")

print("\nUSER: My website gets traffic but no one buys")
print("BOT: Got it. To ensure we're the right fit, what's your monthly marketing budget? We work with businesses investing $300+ per month.")

print("\nUSER: About $500 per month")
print("BOT: Perfect! What's the best email to send you the appointment details?")

print("\nUSER: sarah@example.com")
print("BOT: Great! What day works best for your consultation? We have availability Tuesday through Friday.")

print("\nUSER: Tuesday works best")
print("(All information collected - ready for booking!)")

print("\n=== Budget Too Low Example ===\n")

print("USER: My budget is $200")
print("BOT: I appreciate your honesty! Our programs start at $300/month to ensure we can deliver real results. Would you be open to adjusting your budget in the future?")
print("(Budget too low - staying on budget step)")

print("\n=== Key Features Demonstrated ===")
print("✓ Automatic language detection (Spanish/English)")
print("✓ Natural conversational flow")
print("✓ Step-by-step data collection")
print("✓ Intelligent information extraction")
print("✓ Budget qualification ($300+ requirement)")
print("✓ Smooth transition to booking when all data collected")