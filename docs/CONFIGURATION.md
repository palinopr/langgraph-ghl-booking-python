# Configuration Guide

## Overview

This guide covers all configuration options for the WhatsApp Booking System. The system uses a combination of environment variables, YAML configuration files, and runtime settings to provide flexible configuration management.

## Configuration Hierarchy

The system loads configuration in the following order (later sources override earlier ones):

1. Default values (hardcoded)
2. `config/config.yaml` (business rules)
3. Environment variables
4. Runtime overrides (if applicable)

## Environment Variables

### Required Variables

These must be set for the system to function:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM operations | `sk-proj-...` |
| `GHL_API_KEY` | GoHighLevel API key | `ghl_...` |
| `GHL_LOCATION_ID` | GoHighLevel location/business ID | `loc_abc123` |
| `GHL_WEBHOOK_SECRET` | Secret for webhook signature validation | `random-secret-string` |

### Optional Variables

#### Application Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENVIRONMENT` | Runtime environment | `development` | `production`, `staging` |
| `PORT` | Server port | `8000` | `3000` |
| `HOST` | Server host | `0.0.0.0` | `127.0.0.1` |
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | Log output format | `json` | `text`, `json` |

#### Performance Tuning

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `WORKER_COUNT` | Number of Uvicorn workers | `1` | `4` |
| `MAX_QUEUE_SIZE` | Maximum webhook queue size | `1000` | `5000` |
| `REQUEST_TIMEOUT` | Request timeout in seconds | `30` | `60` |
| `WORKFLOW_TIMEOUT` | LangGraph workflow timeout | `120` | `300` |
| `CONNECTION_POOL_SIZE` | HTTP connection pool size | `10` | `50` |

#### Rate Limiting

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `RATE_LIMIT_PER_MINUTE` | Requests per minute per IP | `30` | `60` |
| `RATE_LIMIT_PER_PHONE` | Requests per minute per phone | `10` | `20` |
| `RATE_LIMIT_BURST` | Burst allowance | `10` | `20` |
| `RATE_LIMIT_STORAGE` | Storage backend | `memory` | `redis` |

#### Monitoring & Tracing

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LANGSMITH_API_KEY` | LangSmith API key for tracing | `None` | `ls_...` |
| `LANGSMITH_TRACING` | Enable LangSmith tracing | `false` | `true` |
| `LANGSMITH_PROJECT` | LangSmith project name | `whatsapp-booking` | `prod-booking` |
| `SENTRY_DSN` | Sentry error tracking DSN | `None` | `https://...@sentry.io/...` |
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` | `false` |

#### Security

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ALLOWED_IPS` | Comma-separated allowed IPs | `*` | `10.0.0.0/8,172.16.0.0/12` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` | `https://app.example.com` |
| `WEBHOOK_SIGNATURE_HEADER` | Header name for signature | `X-GHL-Signature` | `X-Webhook-Signature` |
| `ENABLE_DOCS` | Enable API documentation | `true` | `false` |

#### External Services

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `REDIS_URL` | Redis connection URL | `None` | `redis://localhost:6379` |
| `DATABASE_URL` | Database connection URL | `None` | `postgresql://user:pass@host/db` |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4-turbo-preview` | `gpt-3.5-turbo` |
| `OPENAI_TEMPERATURE` | Model temperature | `0.7` | `0.3` |

## Business Configuration (config.yaml)

The `config/config.yaml` file contains business logic configuration:

### Full Configuration Example

```yaml
# Business Information
business:
  name: "AI Marketing Solutions"
  description: "Professional AI-powered marketing services"
  timezone: "America/Los_Angeles"
  website: "https://example.com"
  support_email: "support@example.com"
  
# Booking Rules
booking:
  # Budget validation
  minimum_budget: 1000
  maximum_budget: 100000
  currency: "USD"
  
  # Appointment settings
  appointment_duration: 30  # minutes
  buffer_time: 15          # minutes between appointments
  max_future_days: 30      # how far ahead to book
  min_notice_hours: 24     # minimum notice before appointment
  
  # Working hours (24-hour format)
  working_hours:
    monday:
      start: "09:00"
      end: "17:00"
    tuesday:
      start: "09:00"
      end: "17:00"
    wednesday:
      start: "09:00"
      end: "17:00"
    thursday:
      start: "09:00"
      end: "17:00"
    friday:
      start: "09:00"
      end: "15:00"
    saturday:
      closed: true
    sunday:
      closed: true
  
  # Holidays (ISO format)
  holidays:
    - "2024-12-25"  # Christmas
    - "2024-01-01"  # New Year
    - "2024-07-04"  # Independence Day
  
  # Appointment types
  appointment_types:
    - name: "Initial Consultation"
      duration: 30
      description: "Free initial consultation"
    - name: "Strategy Session"
      duration: 60
      description: "Deep dive strategy planning"
    - name: "Quick Check-in"
      duration: 15
      description: "Brief follow-up call"

# Validation Rules
validation:
  # Required fields from customer
  required_fields:
    - name
    - goal
    - budget
  
  # Field validation patterns
  patterns:
    phone: "^\\+?[1-9]\\d{1,14}$"  # E.164 format
    email: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  
  # Budget validation messages
  budget_messages:
    below_minimum: "Thank you for your interest! Our services start at $1,000. Would you like to learn about our starter packages?"
    above_maximum: "For projects over $100,000, please contact our enterprise team at enterprise@example.com"
    invalid: "Please provide a valid budget amount to proceed with booking."

# Workflow Configuration
workflow:
  # Node-specific settings
  triage:
    spam_keywords:
      - "free money"
      - "click here"
      - "limited time offer"
      - "viagra"
    min_message_length: 10
    max_message_length: 1000
  
  collect:
    max_attempts: 3
    retry_messages:
      missing_name: "Could you please share your name?"
      missing_goal: "What specific marketing goals do you have?"
      missing_budget: "What's your approximate budget for this project?"
  
  validate:
    strict_mode: true
    allow_flexible_budget: false
  
  booking:
    confirmation_required: false
    send_calendar_invite: true
    reminder_hours: [24, 2]  # Send reminders 24h and 2h before

# Message Templates
messages:
  # Welcome messages
  welcome:
    default: "Hello! I'm here to help you book a consultation. Could you tell me your name and what you're looking for?"
    returning: "Welcome back! How can I help you today?"
  
  # Success messages
  success:
    booking_confirmed: "Great! I've booked your appointment for {date} at {time}. You'll receive a confirmation email shortly."
    email_sent: "A confirmation email has been sent to {email}."
  
  # Error messages
  errors:
    general: "I apologize, but I encountered an issue. Please try again or contact support at {support_email}."
    timeout: "The conversation has timed out. Please start a new conversation."
    invalid_time: "That time slot is not available. Please choose another time."
    
  # Follow-up messages
  followup:
    no_show: "We missed you at your appointment. Would you like to reschedule?"
    post_meeting: "Thank you for meeting with us! How was your experience?"

# Integration Settings
integrations:
  # GoHighLevel specific settings
  ghl:
    calendar_id: "cal_default"
    pipeline_id: "pipe_abc123"
    stage_id: "stage_new_lead"
    tag_ids:
      - "whatsapp-lead"
      - "auto-booked"
    custom_fields:
      lead_source: "WhatsApp"
      booking_type: "Automated"
  
  # Email settings (if using email notifications)
  email:
    from_address: "noreply@example.com"
    from_name: "AI Marketing Solutions"
    reply_to: "support@example.com"

# Feature Flags
features:
  # Enable/disable features
  enable_email_notifications: true
  enable_sms_reminders: false
  enable_calendar_sync: true
  enable_lead_scoring: false
  enable_conversation_history: true
  enable_multilingual: false
  
  # Experimental features
  experimental:
    voice_transcription: false
    sentiment_analysis: false
    predictive_scheduling: false

# Localization
localization:
  default_language: "en"
  supported_languages:
    - "en"
    - "es"
    - "fr"
  date_format: "MM/DD/YYYY"
  time_format: "12h"  # or "24h"
  currency_symbol: "$"
  number_format: "en-US"
```

## Advanced Configuration

### Using Environment-Specific Configs

Create environment-specific configuration files:

```bash
config/
├── config.yaml          # Base configuration
├── config.dev.yaml      # Development overrides
├── config.staging.yaml  # Staging overrides
└── config.prod.yaml     # Production overrides
```

Load based on environment:
```python
# In your config loader
import os
import yaml

def load_config():
    # Load base config
    with open('config/config.yaml') as f:
        config = yaml.safe_load(f)
    
    # Load environment-specific config
    env = os.getenv('ENVIRONMENT', 'development')
    env_config_path = f'config/config.{env}.yaml'
    
    if os.path.exists(env_config_path):
        with open(env_config_path) as f:
            env_config = yaml.safe_load(f)
            # Deep merge configs
            config = deep_merge(config, env_config)
    
    return config
```

### Dynamic Configuration Updates

For configuration that needs to change without restart:

```python
# config/dynamic.py
from typing import Dict, Any
import asyncio
import aiofiles
import yaml

class DynamicConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._last_modified = 0
        self._lock = asyncio.Lock()
    
    async def load(self):
        async with self._lock:
            async with aiofiles.open(self.config_path, 'r') as f:
                content = await f.read()
                self._config = yaml.safe_load(content)
    
    async def get(self, key: str, default=None):
        # Reload if file changed
        if await self._is_modified():
            await self.load()
        
        return self._config.get(key, default)
    
    async def _is_modified(self) -> bool:
        stat = os.stat(self.config_path)
        return stat.st_mtime > self._last_modified
```

### Configuration Validation

Validate configuration on startup:

```python
# config/validator.py
from pydantic import BaseModel, validator
from typing import Dict, List, Optional

class BusinessConfig(BaseModel):
    name: str
    timezone: str
    minimum_budget: float
    maximum_budget: float
    
    @validator('minimum_budget')
    def validate_min_budget(cls, v):
        if v <= 0:
            raise ValueError('Minimum budget must be positive')
        return v
    
    @validator('timezone')
    def validate_timezone(cls, v):
        import pytz
        if v not in pytz.all_timezones:
            raise ValueError(f'Invalid timezone: {v}')
        return v

class ConfigSchema(BaseModel):
    business: BusinessConfig
    booking: Dict
    validation: Dict
    workflow: Dict
    messages: Dict
    
    class Config:
        extra = 'forbid'  # Fail on unknown fields

def validate_config(config: dict) -> ConfigSchema:
    return ConfigSchema(**config)
```

## Configuration Best Practices

### 1. Security

- **Never commit secrets**: Use environment variables for sensitive data
- **Use strong webhook secrets**: Generate with `openssl rand -hex 32`
- **Rotate API keys regularly**: Implement key rotation mechanism
- **Validate all inputs**: Use schema validation for configs

### 2. Environment Management

```bash
# Development
cp .env.example .env.development
# Edit with development values

# Staging
cp .env.example .env.staging
# Edit with staging values

# Production
# Use secret management service (AWS Secrets Manager, etc.)
```

### 3. Configuration Testing

```python
# tests/test_config.py
import pytest
from config import load_config, validate_config

def test_config_loads():
    config = load_config()
    assert config is not None
    assert 'business' in config

def test_config_validates():
    config = load_config()
    validated = validate_config(config)
    assert validated.business.minimum_budget > 0

def test_missing_required_raises():
    invalid_config = {'business': {}}
    with pytest.raises(ValidationError):
        validate_config(invalid_config)
```

### 4. Monitoring Configuration

```yaml
# config/monitoring.yaml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 0.05"
    channels: ["email", "slack"]
  
  - name: "Slow Response Time"
    condition: "p95_latency > 2000"
    channels: ["pagerduty"]

metrics:
  custom:
    - name: "booking_success_rate"
      type: "counter"
      labels: ["status", "appointment_type"]
    
    - name: "workflow_duration"
      type: "histogram"
      buckets: [0.5, 1.0, 2.0, 5.0, 10.0]
```

## Troubleshooting Configuration

### Common Issues

1. **"Configuration key not found"**
   ```python
   # Use default values
   value = config.get('missing_key', 'default_value')
   ```

2. **"Invalid timezone"**
   ```bash
   # List valid timezones
   python -c "import pytz; print(pytz.all_timezones)"
   ```

3. **"Environment variable not set"**
   ```bash
   # Check all environment variables
   env | grep -E "GHL|OPENAI|LANG"
   ```

### Configuration Debugging

```python
# Debug configuration loading
import logging
logging.basicConfig(level=logging.DEBUG)

# In your app
logger.debug(f"Loaded config: {config}")
logger.debug(f"Environment: {os.environ}")
```

### Health Check for Configuration

```python
# api/health.py
@app.get("/health/config")
async def check_config():
    issues = []
    
    # Check required env vars
    for var in ['OPENAI_API_KEY', 'GHL_API_KEY']:
        if not os.getenv(var):
            issues.append(f"Missing {var}")
    
    # Validate config structure
    try:
        config = load_config()
        validate_config(config)
    except Exception as e:
        issues.append(f"Config validation: {str(e)}")
    
    return {
        "healthy": len(issues) == 0,
        "issues": issues
    }
```

---

For more information, see the [deployment guide](DEPLOYMENT.md) or [main documentation](../README.md).