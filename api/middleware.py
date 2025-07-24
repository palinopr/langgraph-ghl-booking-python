"""
Middleware for security, rate limiting, and request validation.
"""
import hmac
import hashlib
import logging
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def create_limiter() -> Limiter:
    """
    Create and configure the rate limiter.
    """
    return Limiter(
        key_func=get_remote_address,
        default_limits=["30/minute"],
        headers_enabled=True,
        strategy="fixed-window"
    )


async def verify_webhook_signature(
    request: Request,
    body: bytes,
    signature: Optional[str] = None
) -> bool:
    """
    Verify webhook signature for security.
    
    Args:
        request: FastAPI request object
        body: Raw request body
        signature: Signature from header or body
        
    Returns:
        bool: True if signature is valid or verification is disabled
    """
    webhook_secret = os.getenv("GHL_WEBHOOK_SECRET")
    
    # If no secret is configured, skip verification (development mode)
    if not webhook_secret:
        logger.warning("Webhook signature verification disabled (no secret configured)")
        return True
    
    # Get signature from header if not in body
    if not signature:
        signature = request.headers.get("X-GHL-Signature") or request.headers.get("X-Webhook-Signature")
    
    if not signature:
        logger.error("No signature provided for webhook verification")
        return False
    
    # Calculate expected signature
    expected_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    is_valid = hmac.compare_digest(signature, expected_signature)
    
    if not is_valid:
        logger.error(f"Invalid webhook signature. Expected: {expected_signature[:10]}..., Got: {signature[:10]}...")
    
    return is_valid


async def logging_middleware(request: Request, call_next):
    """
    Log all incoming requests and responses.
    """
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"Incoming {request.method} request to {request.url.path} from {get_remote_address(request)}")
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Log response
        logger.info(
            f"Request to {request.url.path} completed with status {response.status_code} in {duration:.3f}s"
        )
        
        return response
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"Request to {request.url.path} failed after {duration:.3f}s: {str(e)}",
            exc_info=True
        )
        raise


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global error handler for consistent error responses.
    """
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for validation errors.
    """
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Invalid request data",
            "details": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def setup_middleware(app):
    """
    Configure all middleware for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Create rate limiter
    limiter = create_limiter()
    app.state.limiter = limiter
    
    # Add exception handlers
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(Exception, error_handler)
    app.add_exception_handler(HTTPException, validation_error_handler)
    
    # Add logging middleware
    app.middleware("http")(logging_middleware)
    
    logger.info("Middleware configured successfully")