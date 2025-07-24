"""
Main entry point for the GHL WhatsApp Booking API.
"""
import sys
import os

# Add parent directory to path to import api module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.webhook import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)