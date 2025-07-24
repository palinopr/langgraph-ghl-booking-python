# LangGraph GHL WhatsApp Booking System (Python)

## 🎯 Overview

A production-ready WhatsApp booking system built with Python that automatically schedules appointments through GoHighLevel (GHL). This system processes messages from Meta ads via WhatsApp, collects customer information (name, goal, budget), validates the data against business rules, and books appointments automatically—all without human intervention.

Built using LangGraph for workflow orchestration and FastAPI for webhook handling, this system provides a scalable, type-safe solution for automated appointment booking.

## ✨ Key Features

- **Automated Booking Flow**: Complete end-to-end automation from WhatsApp message to confirmed appointment
- **Intelligent Spam Filtering**: AI-powered triage to filter irrelevant messages
- **Data Extraction**: Smart extraction of customer name, goals, and budget from natural conversations
- **Business Rule Validation**: Configurable rules (e.g., minimum budget requirements)
- **GoHighLevel Integration**: Direct API integration for calendar management and booking
- **Async Processing**: Built on FastAPI for high-performance webhook handling
- **Type Safety**: Full type hints and Pydantic models for runtime validation
- **Production Ready**: Comprehensive error handling, logging, and monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- OpenAI API key
- GoHighLevel API credentials
- Basic understanding of async Python

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/langgraph-ghl-booking-python.git
cd langgraph-ghl-booking-python

# Install dependencies using Poetry
poetry install

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Basic Configuration

1. **Environment Variables** (`.env`):
```env
# Required API Keys
OPENAI_API_KEY=sk-...
GHL_API_KEY=your_ghl_api_key
GHL_LOCATION_ID=your_location_id
GHL_WEBHOOK_SECRET=your_webhook_secret

# Optional Configuration
LANGSMITH_API_KEY=ls_...
LANGSMITH_TRACING=true
ENVIRONMENT=development
PORT=8000
LOG_LEVEL=INFO
```

2. **Business Rules** (`config/config.yaml`):
```yaml
business:
  name: "Your Business Name"
  timezone: "America/Los_Angeles"
  minimum_budget: 1000
  booking:
    appointment_duration: 30  # minutes
    buffer_time: 15          # minutes between appointments
    max_future_days: 30      # how far ahead to book
    
validation:
  required_fields:
    - name
    - goal
    - budget
  budget_messages:
    below_minimum: "Thank you for your interest! Our services start at $1000."
```

### Running the Application

```bash
# Development mode with auto-reload
poetry run uvicorn api.webhook:app --reload --port 8000

# Production mode
poetry run uvicorn api.webhook:app --host 0.0.0.0 --port 8000

# Run with LangGraph CLI (for local testing)
poetry run langgraph dev

# Test the workflow directly
poetry run python scripts/run_workflow.py
```

## 📁 Project Structure

```
langgraph-ghl-booking-python/
├── booking_agent/           # Core LangGraph workflow
│   ├── __init__.py
│   ├── graph.py            # Main workflow definition
│   └── utils/
│       ├── __init__.py
│       ├── state.py        # State definitions
│       ├── nodes.py        # Workflow nodes
│       └── tools.py        # GHL and utility tools
├── api/                    # FastAPI webhook server
│   ├── __init__.py
│   ├── webhook.py          # Main webhook handler
│   ├── models.py           # Pydantic models
│   └── middleware.py       # Auth, rate limiting
├── config/
│   └── config.yaml         # Business configuration
├── tests/                  # Test suite
│   ├── test_nodes.py       # Unit tests for nodes
│   ├── test_workflow.py    # Integration tests
│   └── test_webhook.py     # API endpoint tests
├── scripts/                # Utility scripts
│   ├── run_workflow.py     # Test workflow locally
│   └── test_ghl.py         # Test GHL connection
├── docs/                   # Documentation
│   ├── API.md             # API reference
│   ├── DEPLOYMENT.md      # Deployment guide
│   └── CONFIGURATION.md   # Config reference
├── .env.example           # Environment template
├── pyproject.toml         # Dependencies & config
├── langgraph.json         # LangGraph configuration
└── README.md              # This file
```

## 🔄 Workflow Architecture

The system uses a linear LangGraph workflow with four main nodes:

```
WhatsApp Message → Triage → Collect → Validate → Book
                     ↓         ↓         ↓         ↓
                   Filter   Extract   Check     Create
                   Spam     Data      Rules   Appointment
```

### Node Descriptions

1. **Triage Node**: Filters spam and irrelevant messages using AI
2. **Collect Node**: Extracts customer information from conversation
3. **Validate Node**: Checks business rules and data completeness
4. **Booking Node**: Creates appointment in GoHighLevel

## 🛠️ Development

### Setting Up Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=booking_agent --cov=api

# Type checking
poetry run mypy .

# Linting
poetry run ruff check .
poetry run black .
```

### Testing the Workflow

```bash
# Test a single message through the workflow
poetry run python scripts/run_workflow.py --message "Hi, I need help with marketing. My budget is $2000"

# Test GHL connection
poetry run python scripts/test_ghl.py

# Run webhook locally with test data
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to book an appointment", "from": "+1234567890"}'
```

## 🌐 API Endpoints

### Webhook Endpoint
- **POST** `/webhook` - Receives WhatsApp messages
- **Rate Limit**: 30 requests/minute per IP
- **Authentication**: Webhook secret validation

### Health & Monitoring
- **GET** `/health` - System health check
- **GET** `/metrics` - Prometheus metrics
- **GET** `/status` - Detailed system status

See [docs/API.md](docs/API.md) for complete API documentation.

## 🚢 Deployment

### Quick Deploy Options

1. **LangGraph Cloud** (Recommended)
   ```bash
   poetry run langgraph deploy
   ```

2. **Docker**
   ```bash
   docker build -t ghl-booking .
   docker run -p 8000:8000 --env-file .env ghl-booking
   ```

3. **Cloud Platforms**
   - AWS Lambda (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#aws-lambda))
   - Google Cloud Run (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#google-cloud-run))
   - Railway/Render (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#paas-platforms))

## 📊 Monitoring & Observability

- **Logging**: Structured JSON logs with correlation IDs
- **Tracing**: LangSmith integration for workflow visualization
- **Metrics**: Prometheus metrics for performance monitoring
- **Alerts**: Configurable alerts for failures and SLA breaches

## 🔒 Security

- Webhook signature validation
- Rate limiting per IP and phone number
- Environment variable encryption
- API key rotation support
- Audit logging for all bookings

## 🧪 Testing

The project includes comprehensive tests:

- **Unit Tests**: Individual node testing with mocks
- **Integration Tests**: Full workflow testing
- **API Tests**: Webhook endpoint testing
- **Load Tests**: Performance testing under load

Run all tests:
```bash
poetry run pytest -v
```

## 📚 Documentation

- [API Reference](docs/API.md) - Detailed API documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions
- [Configuration Guide](docs/CONFIGURATION.md) - All configuration options
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Technical implementation details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- Powered by [FastAPI](https://fastapi.tiangolo.com/) for high-performance APIs
- Integrates with [GoHighLevel](https://www.gohighlevel.com/) for CRM functionality

---

**Note**: This is a production-ready system. Ensure all environment variables are properly configured before deployment. For support, please refer to the documentation or open an issue.