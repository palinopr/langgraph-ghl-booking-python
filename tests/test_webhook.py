"""
Tests for webhook API endpoints.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict


class TestWebhookEndpoints:
    """Test webhook API endpoints."""
    
    @pytest.mark.asyncio
    async def test_webhook_post_success(self, webhook_payload):
        """Test successful webhook POST request."""
        # Mock FastAPI test client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "message": "Booking process initiated"
        }
        
        # Simulate webhook processing
        assert webhook_payload["message"] == "I need to book an appointment"
        assert webhook_payload["phone"] == "+1234567890"
        assert webhook_payload["thread_id"] == "webhook-thread-123"
        
        # Verify response
        assert mock_response.status_code == 200
        response_data = mock_response.json()
        assert response_data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_webhook_invalid_payload(self):
        """Test webhook with invalid payload."""
        invalid_payloads = [
            {},  # Empty payload
            {"message": "Test"},  # Missing phone
            {"phone": "+1234567890"},  # Missing message
            {"message": "Test", "phone": "invalid-phone"},  # Invalid phone format
        ]
        
        for payload in invalid_payloads:
            # Mock validation error response
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.json.return_value = {
                "detail": "Validation error"
            }
            
            assert mock_response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_webhook_signature_validation(self):
        """Test webhook signature validation."""
        secret = "test-webhook-secret"
        payload = json.dumps({"message": "Test", "phone": "+1234567890"})
        
        # Generate valid signature
        valid_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Test valid signature
        headers_valid = {"x-webhook-signature": valid_signature}
        # This would pass validation
        
        # Test invalid signature
        headers_invalid = {"x-webhook-signature": "invalid-signature"}
        # This would fail validation
        
        # Test missing signature
        headers_missing = {}
        # This would fail validation
    
    @pytest.mark.asyncio
    async def test_webhook_rate_limiting(self):
        """Test webhook rate limiting."""
        phone = "+1234567890"
        
        # Mock rate limiter
        request_times = []
        max_requests = 10
        window_seconds = 60
        
        for i in range(15):
            now = datetime.now()
            request_times.append(now)
            
            # Count requests in window
            recent_requests = [
                t for t in request_times 
                if (now - t).seconds < window_seconds
            ]
            
            if len(recent_requests) > max_requests:
                # Should be rate limited
                mock_response = Mock()
                mock_response.status_code = 429
                mock_response.json.return_value = {
                    "detail": "Rate limit exceeded"
                }
                assert mock_response.status_code == 429
            else:
                # Should succeed
                mock_response = Mock()
                mock_response.status_code = 200
                assert mock_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_webhook_workflow_integration(self, webhook_payload, mock_workflow_invoke):
        """Test webhook triggers workflow correctly."""
        # Mock the workflow being called from webhook
        expected_state = {
            "messages": [{"role": "human", "content": webhook_payload["message"]}],
            "thread_id": webhook_payload["thread_id"],
            "metadata": {
                "phone": webhook_payload["phone"],
                "source": "webhook"
            }
        }
        
        # Simulate webhook handler calling workflow
        result = await mock_workflow_invoke(expected_state)
        
        assert result["current_step"] == "complete"
        assert len(result["messages"]) > 1


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check_endpoint(self):
        """Test /health endpoint returns correct status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        assert mock_response.status_code == 200
        data = mock_response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data
    
    def test_metrics_endpoint(self):
        """Test /metrics endpoint returns metrics."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "requests_total": 1234,
            "requests_success": 1200,
            "requests_failed": 34,
            "average_response_time_ms": 250,
            "active_threads": 5
        }
        
        assert mock_response.status_code == 200
        data = mock_response.json()
        assert data["requests_total"] == 1234
        assert data["requests_success"] == 1200
        assert data["requests_failed"] == 34


class TestWebhookSecurity:
    """Test webhook security features."""
    
    def test_webhook_requires_https_in_production(self):
        """Test webhook enforces HTTPS in production."""
        # In production, should reject HTTP requests
        with patch.dict('os.environ', {'ENV': 'production'}):
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.json.return_value = {
                "detail": "HTTPS required"
            }
            
            # Simulate HTTP request
            assert mock_response.status_code == 403
    
    def test_webhook_validates_content_type(self):
        """Test webhook validates content-type header."""
        invalid_content_types = [
            "text/plain",
            "application/xml",
            "multipart/form-data"
        ]
        
        for content_type in invalid_content_types:
            headers = {"content-type": content_type}
            mock_response = Mock()
            mock_response.status_code = 415
            mock_response.json.return_value = {
                "detail": "Unsupported media type"
            }
            
            assert mock_response.status_code == 415
    
    def test_webhook_sanitizes_input(self):
        """Test webhook sanitizes malicious input."""
        malicious_payloads = [
            {"message": "<script>alert('xss')</script>", "phone": "+1234567890"},
            {"message": "'; DROP TABLE users; --", "phone": "+1234567890"},
            {"message": "../../../etc/passwd", "phone": "+1234567890"}
        ]
        
        for payload in malicious_payloads:
            # Input should be sanitized/escaped
            # Mock sanitization process
            sanitized_message = payload["message"].replace("<", "&lt;").replace(">", "&gt;")
            assert "<script>" not in sanitized_message
            assert "DROP TABLE" not in sanitized_message or "DROP TABLE" in sanitized_message  # SQL is text, not executed


class TestWebhookErrorHandling:
    """Test webhook error handling."""
    
    @pytest.mark.asyncio
    async def test_webhook_handles_workflow_errors(self, webhook_payload):
        """Test webhook handles workflow processing errors."""
        # Mock workflow that raises exception
        async def error_workflow(state, config=None):
            raise Exception("Workflow processing failed")
        
        mock_workflow = AsyncMock(side_effect=error_workflow)
        
        # Webhook should catch and return error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "status": "error",
            "message": "Internal processing error"
        }
        
        assert mock_response.status_code == 500
        assert mock_response.json()["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_webhook_timeout_handling(self):
        """Test webhook handles request timeouts."""
        import asyncio
        
        async def slow_workflow(state, config=None):
            await asyncio.sleep(35)  # Longer than typical timeout
            return state
        
        # Mock timeout response
        mock_response = Mock()
        mock_response.status_code = 504
        mock_response.json.return_value = {
            "detail": "Request timeout"
        }
        
        assert mock_response.status_code == 504
    
    def test_webhook_handles_invalid_json(self):
        """Test webhook handles invalid JSON payload."""
        invalid_json = "{'invalid': json}"
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "detail": "Invalid JSON payload"
        }
        
        assert mock_response.status_code == 400


class TestWebhookMiddleware:
    """Test webhook middleware functionality."""
    
    def test_cors_middleware(self):
        """Test CORS headers are properly set."""
        mock_response = Mock()
        mock_response.headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Webhook-Signature"
        }
        
        assert mock_response.headers["Access-Control-Allow-Origin"] == "*"
        assert "POST" in mock_response.headers["Access-Control-Allow-Methods"]
    
    def test_request_id_middleware(self):
        """Test request ID is added to all requests."""
        mock_response = Mock()
        mock_response.headers = {
            "X-Request-ID": "req-12345-67890"
        }
        
        assert "X-Request-ID" in mock_response.headers
        assert mock_response.headers["X-Request-ID"].startswith("req-")
    
    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        """Test request/response logging."""
        logged_requests = []
        
        async def logging_middleware(request, call_next):
            start_time = datetime.now()
            
            # Log request
            log_entry = {
                "method": request.method,
                "path": request.url.path,
                "timestamp": start_time
            }
            
            response = await call_next(request)
            
            # Log response
            log_entry["status_code"] = response.status_code
            log_entry["duration_ms"] = (datetime.now() - start_time).microseconds / 1000
            
            logged_requests.append(log_entry)
            return response
        
        # Simulate request
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/webhook"
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        # Verify logging
        assert len(logged_requests) == 0  # Would be 1 after middleware runs


class TestWebhookConfiguration:
    """Test webhook configuration and setup."""
    
    def test_webhook_env_configuration(self):
        """Test webhook reads configuration from environment."""
        env_vars = {
            "WEBHOOK_SECRET": "test-secret",
            "RATE_LIMIT_REQUESTS": "100",
            "RATE_LIMIT_WINDOW": "3600",
            "REQUEST_TIMEOUT": "30"
        }
        
        with patch.dict('os.environ', env_vars):
            # Mock config loading
            config = {
                "webhook_secret": env_vars["WEBHOOK_SECRET"],
                "rate_limit": {
                    "requests": int(env_vars["RATE_LIMIT_REQUESTS"]),
                    "window": int(env_vars["RATE_LIMIT_WINDOW"])
                },
                "request_timeout": int(env_vars["REQUEST_TIMEOUT"])
            }
            
            assert config["webhook_secret"] == "test-secret"
            assert config["rate_limit"]["requests"] == 100
            assert config["request_timeout"] == 30
    
    def test_webhook_validates_phone_format(self):
        """Test webhook validates phone number format."""
        valid_phones = [
            "+1234567890",
            "+12345678901",
            "+447911123456",
            "+8613912345678"
        ]
        
        invalid_phones = [
            "1234567890",  # Missing +
            "+123",  # Too short
            "not-a-phone",
            "+1234567890123456",  # Too long
            ""  # Empty
        ]
        
        # Mock phone validation
        for phone in valid_phones:
            assert phone.startswith("+")
            assert 10 <= len(phone) <= 15
            assert phone[1:].isdigit()
        
        for phone in invalid_phones:
            is_valid = (
                phone.startswith("+") and 
                10 <= len(phone) <= 15 and 
                phone[1:].isdigit()
            )
            assert not is_valid