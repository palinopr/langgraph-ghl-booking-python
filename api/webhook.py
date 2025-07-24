"""
FastAPI webhook server for WhatsApp booking system.
"""
import os
import logging
import asyncio
from typing import Dict
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import uvicorn

from api.models import (
    WebhookRequest,
    WebhookResponse,
    HealthResponse,
    MetricsResponse,
    ErrorResponse
)
from api.middleware import setup_middleware, verify_webhook_signature

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global metrics storage
metrics = {
    "requests": 0,
    "errors": 0,
    "rate_limited": 0,
    "active_threads": 0,
    "start_time": datetime.utcnow()
}

# Store for active threads (in production, use Redis or similar)
active_threads: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    """
    logger.info("Starting WhatsApp Booking Webhook Server...")
    metrics["start_time"] = datetime.utcnow()
    
    # Import workflow dynamically to handle case where it's not yet created
    try:
        from booking_agent.graph import create_booking_workflow
        app.state.workflow = create_booking_workflow()
        logger.info("Workflow loaded successfully")
    except ImportError as e:
        logger.warning(f"Workflow not available - running in API-only mode: {str(e)}")
        app.state.workflow = None
    
    yield
    
    logger.info("Shutting down WhatsApp Booking Webhook Server...")


# Create FastAPI app
app = FastAPI(
    title="WhatsApp Booking Webhook",
    description="Webhook server for automated WhatsApp appointment booking",
    version="1.0.0",
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)


async def get_request_body(request: Request) -> bytes:
    """
    Get raw request body for signature verification.
    """
    return await request.body()


@app.post("/webhook", response_model=WebhookResponse)
async def webhook_handler(
    webhook_request: WebhookRequest,
    request: Request,
    body: bytes = Depends(get_request_body)
):
    """
    Handle incoming WhatsApp webhook messages.
    
    This endpoint:
    1. Verifies the webhook signature
    2. Processes the message through the LangGraph workflow
    3. Returns a response to acknowledge receipt
    """
    metrics["requests"] += 1
    
    try:
        # Verify signature if enabled
        if not await verify_webhook_signature(request, body, webhook_request.signature):
            metrics["errors"] += 1
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        logger.info(f"Processing webhook for thread {webhook_request.thread_id}")
        
        # Store thread as active
        active_threads[webhook_request.thread_id] = {
            "phone": webhook_request.phone,
            "started_at": datetime.utcnow(),
            "last_message": webhook_request.message
        }
        metrics["active_threads"] = len(active_threads)
        
        # Process through workflow if available
        if hasattr(app.state, "workflow") and app.state.workflow:
            try:
                # Run workflow asynchronously
                result = await asyncio.create_task(
                    process_through_workflow(
                        app.state.workflow,
                        webhook_request
                    )
                )
                
                response_message = result.get("response", "Message received and being processed")
                
            except Exception as e:
                logger.error(f"Workflow processing error: {str(e)}", exc_info=True)
                response_message = "Message received, processing will continue"
        else:
            logger.warning("Workflow not available, acknowledging receipt only")
            response_message = "Message received successfully"
        
        return WebhookResponse(
            status="success",
            message=response_message,
            thread_id=webhook_request.thread_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        metrics["errors"] += 1
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        
        return WebhookResponse(
            status="error",
            message="An error occurred processing your message",
            thread_id=webhook_request.thread_id
        )


async def process_through_workflow(workflow, webhook_request: WebhookRequest) -> dict:
    """
    Process the webhook request through the LangGraph workflow.
    
    Args:
        workflow: The compiled LangGraph workflow
        webhook_request: The incoming webhook request
        
    Returns:
        dict: Processing result
    """
    # Import message types
    from langchain_core.messages import HumanMessage
    
    # Prepare initial state with all required fields
    initial_state = {
        "messages": [HumanMessage(content=webhook_request.message)],
        "thread_id": webhook_request.thread_id,
        "customer_name": None,
        "customer_goal": None,
        "customer_budget": None,
        "current_step": "triage",
        "is_spam": False,
        "validation_errors": [],
        "booking_result": None
    }
    
    # Invoke workflow
    config = {"configurable": {"thread_id": webhook_request.thread_id}}
    result = await workflow.ainvoke(initial_state, config)
    
    # Extract response from result
    # Look for the last AI message in the messages list
    response_message = "Processing complete"
    if result.get("messages"):
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and getattr(msg, "__class__", None).__name__ == "AIMessage":
                response_message = msg.content
                break
    
    return {
        "response": response_message,
        "booking_result": result.get("booking_result"),
        "is_spam": result.get("is_spam", False),
        "validation_errors": result.get("validation_errors", [])
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return HealthResponse(
        status="ok",
        version="1.0.0"
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get server metrics for monitoring.
    """
    uptime = (datetime.utcnow() - metrics["start_time"]).total_seconds()
    
    return MetricsResponse(
        requests=metrics["requests"],
        errors=metrics["errors"],
        rate_limited=metrics["rate_limited"],
        active_threads=metrics["active_threads"],
        uptime_seconds=uptime
    )


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "WhatsApp Booking Webhook",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }


# Note: Rate limiting is already applied via middleware
# If you need to apply specific rate limits to the webhook endpoint,
# uncomment and modify the following:
#
# from slowapi import _rate_limit_exceeded_handler
# from slowapi.errors import RateLimitExceeded
# 
# # Remove the @app.post decorator from the webhook_handler above
# # and use this rate-limited version instead:
# 
# @app.post("/webhook", response_model=WebhookResponse)
# @app.state.limiter.limit("30/minute")
# async def webhook_handler(
#     webhook_request: WebhookRequest,
#     request: Request,
#     body: bytes = Depends(get_request_body)
# ):
#     # ... (same implementation as above)


if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run(
        "api.webhook:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )