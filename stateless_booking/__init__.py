"""
Stateless WhatsApp Booking System

A webhook-based booking system where each message is processed independently.
No loops, no recursion, just simple request/response with GHL persistence.
"""

from .webhook_handler import handle_webhook_message
from .ghl_state_manager import GHLStateManager
from .message_processor import MessageProcessor

__version__ = "2.0.0"  # Major version bump for architectural change
__all__ = ["handle_webhook_message", "GHLStateManager", "MessageProcessor"]