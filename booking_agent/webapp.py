"""FastAPI webhook server integrated with LangGraph for WhatsApp booking system."""
import os
import logging
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global workflow instance
booking_workflow = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - load workflow on startup.
    """
    global booking_workflow
    logger.info("Starting WhatsApp Booking Webhook Server...")
    
    try:
        from booking_agent.graph import create_booking_workflow
        booking_workflow = create_booking_workflow()
        logger.info("Workflow loaded successfully")
    except ImportError as e:
        logger.error(f"Failed to load workflow: {str(e)}")
        raise
    
    yield
    
    logger.info("Shutting down WhatsApp Booking Webhook Server...")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="WhatsApp Booking Webhook",
    description="LangGraph-integrated webhook for automated WhatsApp appointment booking",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/webhook")
async def webhook_handler(
    request: Request,
    x_webhook_secret: str = Header(None, alias="x-webhook-secret")
):
    """
    Handle incoming WhatsApp webhook messages.
    
    This endpoint:
    1. Verifies the webhook secret
    2. Converts the message to LangChain format
    3. Processes through the LangGraph workflow
    4. Returns a response
    """
    # Verify webhook secret
    expected_secret = os.getenv("GHL_WEBHOOK_SECRET")
    if expected_secret and x_webhook_secret != expected_secret:
        logger.warning("Invalid webhook secret provided")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    try:
        # Parse request body
        webhook_data = await request.json()
        logger.info(f"Received webhook data: {webhook_data}")
        
        # Extract message and thread ID from webhook data
        # Handle different possible webhook formats
        message = webhook_data.get("message") or webhook_data.get("text", "")
        thread_id = webhook_data.get("thread_id") or webhook_data.get("phone") or "default"
        phone = webhook_data.get("phone") or thread_id
        
        if not message:
            logger.error("No message content in webhook data")
            raise HTTPException(status_code=400, detail="No message content provided")
        
        # Create initial state with proper LangChain message format
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "thread_id": thread_id,
            "customer_name": None,
            "customer_goal": None,
            "customer_pain_point": None,
            "customer_budget": None,
            "customer_email": None,
            "preferred_day": None,
            "preferred_time": None,
            "available_slots": None,
            "collection_step": None,
            "language": None,
            "current_step": "triage",
            "is_spam": False,
            "validation_errors": [],
            "booking_result": None
        }
        
        # Invoke workflow
        config = {"configurable": {"thread_id": thread_id}}
        result = await booking_workflow.ainvoke(initial_state, config)
        
        # Extract response from result
        response_message = "Message received and processed"
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, "content") and msg.type == "ai":
                    response_message = msg.content
                    break
        
        # Return response
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": response_message,
                "thread_id": thread_id,
                "booking_result": result.get("booking_result")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An error occurred processing your message",
                "error": str(e)
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "workflow_loaded": booking_workflow is not None
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "WhatsApp Booking Webhook (LangGraph)",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    }