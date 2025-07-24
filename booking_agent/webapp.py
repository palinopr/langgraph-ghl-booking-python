"""FastAPI webhook server with STATELESS handler for WhatsApp booking system."""
import os
import logging
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stateless_booking.webhook_handler import handle_webhook_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    """
    logger.info("Starting WhatsApp Booking Webhook Server (STATELESS)...")
    yield
    logger.info("Shutting down WhatsApp Booking Webhook Server...")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="WhatsApp Booking Webhook (STATELESS)",
    description="Stateless webhook handler for automated WhatsApp appointment booking",
    version="2.0.0",
    lifespan=lifespan
)

@app.post("/webhook")
async def webhook_handler(
    request: Request,
    x_webhook_secret: str = Header(None, alias="x-webhook-secret")
):
    """
    Handle incoming WhatsApp webhook messages with STATELESS handler.
    
    This endpoint:
    1. Verifies the webhook secret
    2. Processes ONE message atomically (NO LOOPS)
    3. Returns a response and exits
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
        
        # Prepare data for stateless handler
        handler_data = {
            "phone": webhook_data.get("phone", ""),
            "message": webhook_data.get("message") or webhook_data.get("text", ""),
            "conversationId": webhook_data.get("conversationId")
        }
        
        logger.info(f"Processing with stateless handler: {handler_data}")
        
        # Process with STATELESS handler - NO LOOPS!
        result = await handle_webhook_message(handler_data)
        
        logger.info(f"Stateless handler result: {result}")
        
        # Return response
        return JSONResponse(
            status_code=200,
            content=result
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
        "version": "2.0.0",
        "handler": "stateless"
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "WhatsApp Booking Webhook (STATELESS)",
        "version": "2.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    }