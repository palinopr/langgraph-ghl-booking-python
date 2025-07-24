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
    
    # No workflow needed - using stateless handler
    logger.info("Using stateless webhook handler")
    
    yield
    
    logger.info("Shutting down WhatsApp Booking Webhook Server...")


# Create FastAPI app
app = FastAPI(
    title="WhatsApp Booking Webhook",
    description="Webhook server for automated WhatsApp appointment booking - Stateless Architecture",
    version="2.0.0",
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
        # Verify webhook secret if enabled
        if not await verify_webhook_signature(request, body):
            metrics["errors"] += 1
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
        logger.info(f"Processing webhook for thread {webhook_request.thread_id}")
        
        # Store thread as active
        active_threads[webhook_request.thread_id] = {
            "phone": webhook_request.phone,
            "started_at": datetime.utcnow(),
            "last_message": webhook_request.message
        }
        metrics["active_threads"] = len(active_threads)
        
        # Process through stateless handler
        try:
            from stateless_booking import handle_webhook_message
            
            # Prepare data for stateless handler
            webhook_data = {
                "phone": webhook_request.phone,
                "message": webhook_request.message
            }
            
            result = await handle_webhook_message(webhook_data)
            response_message = result.get("message", "Message processed")
            
        except Exception as e:
            logger.error(f"Stateless handler error: {str(e)}", exc_info=True)
            response_message = "An error occurred processing your message"
        
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


# REMOVED - No longer using workflow approach


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return HealthResponse(
        status="ok",
        version="2.0.0"
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
        "version": "2.0.0",
        "architecture": "stateless",
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