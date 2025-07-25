"""
AI Conversation Engine - The intelligence behind our $300/month solution.
"""
import os
import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)

# AI System Prompt
AI_SYSTEM_PROMPT = """
You are an AI assistant for AI Outlet Media, specializing in AI automation solutions.

Keep responses SHORT (2-3 sentences). Be professional, not salesy.

Services we offer:
- AI WhatsApp Automation ($300-1000/month)
- AI Customer Service Bots ($500-1500/month)  
- AI Sales Automation ($800-2000/month)
- AI Workflow Automation ($500-1500/month)
- Custom AI Solutions ($1000-5000/month)

Your approach:
1. Answer questions directly
2. Ask one qualifying question
3. Focus on their automation needs
4. Note their business processes

For each message:
- Give a short, professional response
- Take notes about their automation needs
- Identify what processes they want to automate
- Track budget and timeline

IMPORTANT: Respond ONLY with a valid JSON object. No markdown, no extra text, just the JSON.
Example:
{"response": "Your 2-3 sentence message", "notes": "Notes about automation needs", "insights": "Customer insights", "pain_points": ["automation pain points"], "interests": ["specific services"], "qualification_score": 5, "objections": [], "next_action": "gather_requirements", "missing_info": ["business type", "budget", "timeline"]}
"""


class AIConversationEngine:
    """Intelligent conversation engine powered by GPT-4."""
    
    def __init__(self):
        """Initialize with OpenAI GPT-4."""
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
    @traceable(name="ai_process_message", run_type="chain")
    async def process_message(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        customer_state: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process message with full AI intelligence.
        Returns: response, notes, insights, next_action
        """
        # Build conversation context
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get("role", "customer")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
        
        # Build customer state context
        state_text = ""
        if customer_state:
            state_text = f"""
Current customer information:
- Name: {customer_state.get('customer_name', 'Unknown')}
- Goal: {customer_state.get('customer_goal', 'Not specified')}
- Budget: {customer_state.get('customer_budget', 'Not specified')}
- Pain Point: {customer_state.get('customer_pain_point', 'Not specified')}
- Email: {customer_state.get('customer_email', 'Not provided')}
- Language: {customer_state.get('language', 'en')}
- Current Step: {customer_state.get('booking_step', 'greeting')}
"""
        
        # Create prompt
        user_message = f"""
Conversation history:
{history_text}

{state_text}

Customer message: {message}

Generate a response in JSON format as specified in the system prompt."""
        
        try:
            # Get AI response
            messages = [
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            ai_response = json.loads(response.content)
            
            # Ensure all required fields
            return {
                "response": ai_response.get("response", "I'd be happy to help you with that!"),
                "notes": ai_response.get("notes", ""),
                "insights": ai_response.get("insights", ""),
                "pain_points": ai_response.get("pain_points", []),
                "interests": ai_response.get("interests", []),
                "qualification_score": ai_response.get("qualification_score", 0),
                "objections": ai_response.get("objections", []),
                "next_action": ai_response.get("next_action", "continue_conversation"),
                "missing_info": ai_response.get("missing_info", [])
            }
            
        except json.JSONDecodeError as e:
            # If AI doesn't return valid JSON, try to extract the content
            logger.warning(f"AI didn't return valid JSON: {e}")
            logger.warning(f"Raw response: {response.content}")
            
            # Try to clean and parse the response
            content = response.content
            if "```json" in content:
                # Extract JSON from markdown
                content = content.split("```json")[1].split("```")[0].strip()
                try:
                    ai_response = json.loads(content)
                    return {
                        "response": ai_response.get("response", "I'd be happy to help you with that!"),
                        "notes": ai_response.get("notes", ""),
                        "insights": ai_response.get("insights", ""),
                        "pain_points": ai_response.get("pain_points", []),
                        "interests": ai_response.get("interests", []),
                        "qualification_score": ai_response.get("qualification_score", 0),
                        "objections": ai_response.get("objections", []),
                        "next_action": ai_response.get("next_action", "continue_conversation"),
                        "missing_info": ai_response.get("missing_info", [])
                    }
                except:
                    pass
            
            return {
                "response": "I'd be happy to help you with that!",
                "notes": "AI response was not in expected format",
                "insights": "",
                "pain_points": [],
                "interests": [],
                "qualification_score": 0,
                "objections": [],
                "next_action": "continue_conversation",
                "missing_info": []
            }
        except Exception as e:
            logger.error(f"AI processing error: {str(e)}")
            return {
                "response": "I'd be happy to help you with your marketing needs. What specific goals are you looking to achieve?",
                "notes": f"Error in AI processing: {str(e)}",
                "insights": "",
                "pain_points": [],
                "interests": [],
                "qualification_score": 0,
                "objections": [],
                "next_action": "continue_conversation",
                "missing_info": []
            }


# Quick test function
async def test_ai_engine():
    """Test the AI engine with SEO question."""
    engine = AIConversationEngine()
    
    # Test automation question
    result = await engine.process_message(
        message="Do you do automation?",
        conversation_history=[],
        customer_state={"language": "en", "booking_step": "greeting"}
    )
    
    print("Customer: Do you do automation?")
    print(f"AI: {result['response']}")
    print(f"\nNotes: {result['notes']}")
    print(f"Interests: {result['interests']}")
    print(f"Next Action: {result['next_action']}")
    
    return result


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables
    asyncio.run(test_ai_engine())