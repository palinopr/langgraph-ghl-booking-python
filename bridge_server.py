"""
Bridge server to connect GHL webhooks to LangGraph Cloud.

This FastAPI server receives webhooks from GoHighLevel and forwards them
to LangGraph Cloud for processing via the API.
"""
import os
import json
import logging
import httpx
import asyncio
from typing import Dict, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "https://ghl-python-booking-c30b52e8c48d5005b60fdf394ffbe3aa.us.langgraph.app")
LANGGRAPH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
GHL_WEBHOOK_SECRET = os.getenv("GHL_WEBHOOK_SECRET", "")
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "agent")


class WebhookRequest(BaseModel):
    """GHL webhook request format."""
    message: str = Field(..., description="The incoming WhatsApp message")
    phone: str = Field(..., description="Phone number of the sender")
    conversationId: str = Field(..., description="GHL conversation ID")
    
    # Optional GHL fields
    type: Optional[str] = Field(None, description="Message type")
    locationId: Optional[str] = Field(None, description="GHL location ID")
    contactId: Optional[str] = Field(None, description="GHL contact ID")
    name: Optional[str] = Field(None, description="Contact name")
    email: Optional[str] = Field(None, description="Contact email")
    messageType: Optional[str] = Field(None, description="Message type")
    direction: Optional[str] = Field(None, description="Message direction")
    dateAdded: Optional[str] = Field(None, description="Message timestamp")


class WebhookResponse(BaseModel):
    """Response to GHL webhook."""
    status: str
    message: str
    thread_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting GHL-LangGraph Bridge Server...")
    logger.info(f"LangGraph URL: {LANGGRAPH_URL}")
    logger.info(f"Assistant ID: {ASSISTANT_ID}")
    yield
    logger.info("Shutting down bridge server...")


# Create FastAPI app
app = FastAPI(
    title="GHL-LangGraph Bridge",
    description="Bridge server to connect GoHighLevel webhooks to LangGraph Cloud",
    version="1.0.0",
    lifespan=lifespan
)


async def verify_webhook_secret(request: Request) -> bool:
    """Verify GHL webhook secret."""
    if not GHL_WEBHOOK_SECRET:
        logger.warning("Webhook secret verification disabled (no secret configured)")
        return True
    
    provided_secret = request.headers.get("x-webhook-secret")
    if not provided_secret:
        logger.error("No webhook secret provided in x-webhook-secret header")
        return False
    
    is_valid = provided_secret == GHL_WEBHOOK_SECRET
    if not is_valid:
        logger.error(f"Invalid webhook secret")
    
    return is_valid


async def call_langgraph_api(webhook_request: WebhookRequest) -> Dict:
    """
    Call LangGraph Cloud API to process the message.
    
    Args:
        webhook_request: The incoming webhook request
        
    Returns:
        dict: The response from LangGraph
    """
    async with httpx.AsyncClient() as client:
        # Prepare the input for LangGraph
        langgraph_input = {
            "input": {
                "messages": [
                    {
                        "type": "human",
                        "content": webhook_request.message
                    }
                ],
                "thread_id": webhook_request.conversationId,
                "customer_name": webhook_request.name,
                "customer_phone": webhook_request.phone
            },
            "config": {
                "configurable": {
                    "thread_id": webhook_request.conversationId
                }
            },
            "assistant_id": ASSISTANT_ID,
            "stream_mode": "values"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": LANGGRAPH_API_KEY
        }
        
        try:
            # Try different authentication methods
            for auth_header in ["X-Api-Key", "x-api-key", "Authorization"]:
                if auth_header == "Authorization":
                    headers[auth_header] = f"Bearer {LANGGRAPH_API_KEY}"
                else:
                    headers[auth_header] = LANGGRAPH_API_KEY
                
                logger.info(f"Calling LangGraph API with {auth_header} header...")
                
                response = await client.post(
                    f"{LANGGRAPH_URL}/runs/stream",
                    json=langgraph_input,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("Successfully called LangGraph API")
                    
                    # Handle streaming response
                    chunks = []
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk_data = json.loads(line)
                                chunks.append(chunk_data)
                            except json.JSONDecodeError:
                                logger.debug(f"Non-JSON line: {line}")
                    
                    return {"success": True, "data": chunks, "streaming": True}
                elif response.status_code != 403:
                    logger.error(f"LangGraph API error: {response.status_code} - {response.text}")
                    return {"success": False, "error": response.text}
        
        except Exception as e:
            logger.error(f"Error calling LangGraph API: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Authentication failed with all methods"}


@app.post("/webhook", response_model=WebhookResponse)
async def webhook_handler(
    webhook_request: WebhookRequest,
    request: Request
):
    """
    Handle incoming GHL webhooks and forward to LangGraph.
    
    This endpoint:
    1. Verifies the webhook secret
    2. Forwards the message to LangGraph Cloud
    3. Returns a response to GHL
    """
    logger.info(f"Received webhook for conversation {webhook_request.conversationId}")
    
    # Verify webhook secret
    if not await verify_webhook_secret(request):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    # Call LangGraph API
    result = await call_langgraph_api(webhook_request)
    
    if result["success"]:
        # Extract response message from LangGraph result
        response_message = "Thank you! I'm processing your request and will get back to you shortly."
        
        # Handle streaming response
        if result.get("streaming") and isinstance(result["data"], list):
            # Look through all chunks for the final state
            for chunk in result["data"]:
                if isinstance(chunk, dict):
                    # Check if this chunk has messages
                    messages = chunk.get("messages", [])
                    for msg in reversed(messages):
                        if isinstance(msg, dict) and msg.get("type") == "ai" and msg.get("content"):
                            response_message = msg["content"]
                            break
                    
                    # Also check for booking result
                    if chunk.get("booking_result") and chunk["booking_result"].get("success"):
                        response_message = chunk["booking_result"].get("message", response_message)
        
        return WebhookResponse(
            status="success",
            message=response_message,
            thread_id=webhook_request.conversationId
        )
    else:
        logger.error(f"Failed to process through LangGraph: {result.get('error')}")
        
        # Return a graceful response to GHL even if LangGraph fails
        return WebhookResponse(
            status="success",
            message="Thank you for your message. Our team will reach out to you shortly.",
            thread_id=webhook_request.conversationId
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "GHL-LangGraph Bridge",
        "version": "1.0.0",
        "langgraph_url": LANGGRAPH_URL,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "GHL-LangGraph Bridge Server",
        "version": "1.0.0",
        "description": "Bridge between GoHighLevel webhooks and LangGraph Cloud",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "docs": "/docs"
        },
        "configuration": {
            "langgraph_url": LANGGRAPH_URL,
            "assistant_id": ASSISTANT_ID,
            "webhook_secret_configured": bool(GHL_WEBHOOK_SECRET)
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "bridge_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )