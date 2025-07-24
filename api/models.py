"""
Pydantic models for webhook requests and responses.
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class WebhookRequest(BaseModel):
    """
    Request model for webhook endpoint - matches GHL webhook format.
    """
    # Required fields from GHL
    message: str = Field(..., description="The incoming WhatsApp message")
    phone: str = Field(..., description="Phone number of the sender")
    conversationId: str = Field(..., description="GHL conversation ID")
    
    # Optional fields from GHL
    type: Optional[str] = Field(None, description="Message type (e.g., InboundMessage)")
    locationId: Optional[str] = Field(None, description="GHL location ID")
    contactId: Optional[str] = Field(None, description="GHL contact ID")
    name: Optional[str] = Field(None, description="Contact name")
    email: Optional[str] = Field(None, description="Contact email")
    messageType: Optional[str] = Field(None, description="Message type (e.g., WhatsApp)")
    direction: Optional[str] = Field(None, description="Message direction")
    dateAdded: Optional[str] = Field(None, description="Message timestamp")
    
    # For backward compatibility
    @property
    def thread_id(self) -> str:
        """Map conversationId to thread_id for internal use."""
        return self.conversationId


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