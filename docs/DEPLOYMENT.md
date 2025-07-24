# Deployment Guide

## Overview

This guide covers multiple deployment options for the WhatsApp Booking System, from local development to production cloud deployments. Choose the deployment method that best fits your infrastructure and scaling needs.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Preparation](#environment-preparation)
3. [Deployment Options](#deployment-options)
   - [LangGraph Cloud](#langgraph-cloud-recommended)
   - [Docker](#docker-deployment)
   - [AWS Lambda](#aws-lambda)
   - [Google Cloud Run](#google-cloud-run)
   - [Render](#paas-platforms)
   - [Kubernetes](#kubernetes)
4. [Production Checklist](#production-checklist)
5. [Monitoring & Maintenance](#monitoring--maintenance)

## Prerequisites

Before deploying, ensure you have:

1. **API Keys**:
   - OpenAI API key
   - GoHighLevel API key and location ID
   - Webhook secret for signature validation
   - (Optional) LangSmith API key for tracing

2. **Domain & SSL**:
   - A domain name for webhook URL
   - SSL certificate (auto-provisioned on most platforms)

3. **Deployment Tools**:
   ```bash
   # Install required tools
   pip install poetry
   pip install langgraph-cli  # For LangGraph Cloud
   ```

## Environment Preparation

### 1. Create Production Environment File

```bash
# Copy template
cp .env.example .env.production

# Edit with production values
nano .env.production
```

### 2. Production Environment Variables

```env
# API Keys (Required)
OPENAI_API_KEY=sk-prod-...
GHL_API_KEY=ghl_prod_...
GHL_LOCATION_ID=loc_prod_...
GHL_WEBHOOK_SECRET=strong-random-secret

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000

# Performance Tuning
WORKER_COUNT=4
MAX_QUEUE_SIZE=1000
REQUEST_TIMEOUT=30

# Monitoring (Recommended)
LANGSMITH_API_KEY=ls_prod_...
LANGSMITH_TRACING=true
SENTRY_DSN=https://...@sentry.io/...

# Security
ALLOWED_IPS=10.0.0.0/8,172.16.0.0/12
RATE_LIMIT_PER_MINUTE=60
```

### 3. Build for Production

```bash
# Install production dependencies only
poetry install --only main

# Build application
poetry build

# Run production checks
poetry run python -m pytest
poetry run mypy .
poetry run ruff check .
```

## Deployment Options

### LangGraph Cloud (Recommended)

The easiest deployment option with built-in scaling and monitoring.

#### 1. Configure LangGraph

Create `langgraph.json`:
```json
{
  "name": "whatsapp-booking-system",
  "version": "1.0.0",
  "description": "Automated WhatsApp booking system",
  "runtime": "python:3.11",
  "entry": "booking_agent.graph",
  "env": {
    "file": ".env.production"
  }
}
```

#### 2. Deploy

```bash
# Login to LangGraph Cloud
langgraph auth login

# Deploy application
langgraph deploy --env production

# View deployment status
langgraph status

# View logs
langgraph logs --follow
```

#### 3. Configure Webhook

Update your GHL webhook URL to:
```
https://your-app.langgraph.cloud/webhook
```

### Docker Deployment

For self-hosted deployments with full control.

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start application
CMD ["uvicorn", "api.webhook:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### 2. Build and Run

```bash
# Build image
docker build -t whatsapp-booking:latest .

# Run container
docker run -d \
  --name whatsapp-booking \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  whatsapp-booking:latest

# View logs
docker logs -f whatsapp-booking
```

#### 3. Docker Compose (with dependencies)

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  # Optional: Redis for caching
  redis:
    image: redis:alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  # Optional: Prometheus for metrics
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

volumes:
  redis_data:
  prometheus_data:
```

### AWS Lambda

Serverless deployment for automatic scaling.

#### 1. Install Mangum Adapter

```bash
poetry add mangum
```

#### 2. Create Lambda Handler

Create `lambda_handler.py`:
```python
from mangum import Mangum
from api.webhook import app

# Lambda handler
handler = Mangum(app)
```

#### 3. Create SAM Template

`template.yaml`:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 30
    MemorySize: 512
    Runtime: python3.11

Resources:
  BookingFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.handler
      Environment:
        Variables:
          OPENAI_API_KEY: !Ref OpenAIApiKey
          GHL_API_KEY: !Ref GHLApiKey
          GHL_LOCATION_ID: !Ref GHLLocationId
          GHL_WEBHOOK_SECRET: !Ref WebhookSecret
      Events:
        Webhook:
          Type: Api
          Properties:
            Path: /webhook
            Method: POST
        Health:
          Type: Api
          Properties:
            Path: /health
            Method: GET

Parameters:
  OpenAIApiKey:
    Type: String
    NoEcho: true
  GHLApiKey:
    Type: String
    NoEcho: true
  GHLLocationId:
    Type: String
  WebhookSecret:
    Type: String
    NoEcho: true

Outputs:
  WebhookUrl:
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/webhook"
```

#### 4. Deploy with SAM

```bash
# Build
sam build

# Deploy
sam deploy --guided \
  --parameter-overrides \
    OpenAIApiKey=$OPENAI_API_KEY \
    GHLApiKey=$GHL_API_KEY \
    GHLLocationId=$GHL_LOCATION_ID \
    WebhookSecret=$GHL_WEBHOOK_SECRET
```

### Google Cloud Run

Fully managed serverless container platform.

#### 1. Build Container

```bash
# Configure gcloud
gcloud config set project YOUR_PROJECT_ID

# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/whatsapp-booking
```

#### 2. Deploy to Cloud Run

```bash
gcloud run deploy whatsapp-booking \
  --image gcr.io/YOUR_PROJECT_ID/whatsapp-booking \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY \
  --set-env-vars GHL_API_KEY=$GHL_API_KEY \
  --set-env-vars GHL_LOCATION_ID=$GHL_LOCATION_ID \
  --set-env-vars GHL_WEBHOOK_SECRET=$GHL_WEBHOOK_SECRET \
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --concurrency 100 \
  --max-instances 10
```

#### 3. Configure Custom Domain

```bash
gcloud run domain-mappings create \
  --service whatsapp-booking \
  --domain your-domain.com \
  --region us-central1
```

### PaaS Platforms

#### Render

1. **Create `render.yaml`**:
   ```yaml
   services:
     - type: web
       name: whatsapp-booking
       env: python
       buildCommand: "pip install poetry && poetry install --only main"
       startCommand: "uvicorn api.webhook:app --host 0.0.0.0 --port $PORT"
       envVars:
         - key: PYTHON_VERSION
           value: 3.11.0
         - key: OPENAI_API_KEY
           sync: false
         - key: GHL_API_KEY
           sync: false
         - key: GHL_LOCATION_ID
           sync: false
         - key: GHL_WEBHOOK_SECRET
           sync: false
   ```

2. **Deploy via Dashboard**:
   - Connect GitHub repository
   - Add environment variables
   - Deploy

### Kubernetes

For large-scale deployments with advanced orchestration needs.

#### 1. Create Kubernetes Manifests

`k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whatsapp-booking
spec:
  replicas: 3
  selector:
    matchLabels:
      app: whatsapp-booking
  template:
    metadata:
      labels:
        app: whatsapp-booking
    spec:
      containers:
      - name: app
        image: your-registry/whatsapp-booking:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-key
        - name: GHL_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: ghl-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: whatsapp-booking
spec:
  selector:
    app: whatsapp-booking
  ports:
    - port: 80
      targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: whatsapp-booking-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: whatsapp-booking
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace booking-system

# Create secrets
kubectl create secret generic api-secrets \
  --from-literal=openai-key=$OPENAI_API_KEY \
  --from-literal=ghl-key=$GHL_API_KEY \
  -n booking-system

# Apply manifests
kubectl apply -f k8s/ -n booking-system

# Check status
kubectl get pods -n booking-system
kubectl get svc -n booking-system
```

## Production Checklist

### Before Going Live

- [ ] **Security**
  - [ ] SSL certificate configured
  - [ ] Webhook signature validation enabled
  - [ ] API keys stored securely (not in code)
  - [ ] Rate limiting configured
  - [ ] Input validation on all endpoints

- [ ] **Performance**
  - [ ] Load testing completed
  - [ ] Auto-scaling configured
  - [ ] Connection pooling enabled
  - [ ] Caching strategy implemented
  - [ ] Database indexes optimized

- [ ] **Monitoring**
  - [ ] Health checks configured
  - [ ] Logging to centralized system
  - [ ] Metrics collection enabled
  - [ ] Alerts configured for failures
  - [ ] Error tracking (Sentry) enabled

- [ ] **Reliability**
  - [ ] Retry logic implemented
  - [ ] Circuit breakers configured
  - [ ] Graceful shutdown handling
  - [ ] Backup webhook endpoint
  - [ ] Disaster recovery plan

- [ ] **Compliance**
  - [ ] Data privacy policies implemented
  - [ ] GDPR compliance (if applicable)
  - [ ] Audit logging enabled
  - [ ] Data retention policies configured

## Monitoring & Maintenance

### 1. Set Up Monitoring

```bash
# Prometheus configuration
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'whatsapp-booking'
    static_configs:
      - targets: ['app:8000']
EOF

# Grafana dashboard
# Import dashboard ID: 12345 (FastAPI metrics)
```

### 2. Configure Alerts

```yaml
# alerting-rules.yml
groups:
  - name: booking-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(webhook_requests_total{status="error"}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowProcessing
        expr: histogram_quantile(0.95, booking_duration_seconds_bucket) > 5
        for: 10m
        annotations:
          summary: "Slow booking processing detected"
```

### 3. Maintenance Tasks

```bash
# Daily health check
curl https://your-domain.com/health

# Check logs for errors
kubectl logs -l app=whatsapp-booking --tail=100 | grep ERROR

# Update dependencies
poetry update

# Rotate secrets
kubectl create secret generic api-secrets \
  --from-literal=openai-key=$NEW_OPENAI_KEY \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 4. Scaling Guidelines

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU Usage | > 70% | Add more replicas |
| Memory Usage | > 80% | Increase memory limits |
| Response Time | > 2s | Check external API latency |
| Queue Length | > 100 | Increase worker count |
| Error Rate | > 5% | Check logs and alerts |

## Troubleshooting

### Common Deployment Issues

1. **"Failed to start workers"**
   ```bash
   # Check available resources
   kubectl describe nodes
   # Increase memory/CPU limits
   ```

2. **"Connection refused"**
   ```bash
   # Check service endpoints
   kubectl get endpoints
   # Verify port configuration
   ```

3. **"Webhook timeout"**
   ```bash
   # Increase timeout values
   # Check network policies
   # Verify external API connectivity
   ```

### Debug Commands

```bash
# View application logs
kubectl logs -f deployment/whatsapp-booking

# Execute commands in container
kubectl exec -it deployment/whatsapp-booking -- /bin/bash

# Check environment variables
kubectl exec deployment/whatsapp-booking -- env | grep -E "GHL|OPENAI"

# Test connectivity
kubectl exec deployment/whatsapp-booking -- curl -I https://api.openai.com
```

---

For additional support, refer to the [main documentation](../README.md) or [configuration guide](CONFIGURATION.md).