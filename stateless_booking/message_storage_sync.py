"""
Local message storage for WhatsApp conversation history.
Synchronous version without aiofiles dependency.
"""
import json
import os
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MessageStorage:
    """Store WhatsApp messages locally for conversation history."""
    
    def __init__(self, storage_dir: str = "conversation_history"):
        """Initialize message storage."""
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_file_path(self, contact_id: str) -> str:
        """Get file path for a contact's conversation history."""
        return os.path.join(self.storage_dir, f"{contact_id}.json")
    
    async def save_message(self, contact_id: str, message: Dict[str, Any]) -> None:
        """Save a message to conversation history."""
        file_path = self._get_file_path(contact_id)
        
        # Load existing history
        history = await self.get_messages(contact_id)
        
        # Add new message
        history.append({
            "role": message.get("role", "customer"),
            "content": message.get("content", ""),
            "timestamp": message.get("timestamp", datetime.utcnow().isoformat()),
            "messageType": message.get("messageType", "WhatsApp")
        })
        
        # Keep only last 20 messages
        history = history[-20:]
        
        # Save to file synchronously
        with open(file_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Saved message for contact {contact_id}")
    
    async def get_messages(self, contact_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a contact."""
        file_path = self._get_file_path(contact_id)
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r') as f:
                history = json.load(f)
                # Return last N messages
                return history[-limit:]
        except Exception as e:
            logger.error(f"Error reading history for {contact_id}: {e}")
            return []
    
    async def clear_history(self, contact_id: str) -> None:
        """Clear conversation history for a contact."""
        file_path = self._get_file_path(contact_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleared history for contact {contact_id}")