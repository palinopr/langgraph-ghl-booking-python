"""
Pydantic models for webhook requests and responses.
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class WebhookRequest(BaseModel):
    """
    Request model for webhook endpoint.
    """
    message: str = Field(..., description="The incoming WhatsApp message")
    phone: str = Field(..., description="Phone number of the sender")
    thread_id: str = Field(..., description="Unique thread identifier for conversation tracking")
    signature: Optional[str] = Field(None, description="Optional signature for request verification")


class WebhookResponse(BaseModel):
    """
    Response model for webhook endpoint.
    """
    status: str = Field(..., description="Request status (success/error)")
    message: str = Field(..., description="Response message")
    thread_id: str = Field(..., description="Thread ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.
    """
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")


class MetricsResponse(BaseModel):
    """
    Response model for metrics endpoint.
    """
    requests: int = Field(..., description="Total number of requests processed")
    errors: int = Field(..., description="Total number of errors")
    rate_limited: int = Field(..., description="Number of rate-limited requests")
    active_threads: int = Field(..., description="Number of active conversation threads")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    """
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")