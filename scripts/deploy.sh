#!/bin/bash

# Deployment script for GHL Booking API
# Supports multiple deployment targets: Docker, Cloud Run, AWS ECS, Railway

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ghl-booking-api"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io}"
DOCKER_IMAGE="${DOCKER_IMAGE:-${DOCKER_REGISTRY}/${GITHUB_REPOSITORY:-ai-outlet-media/langgraph-ghl-booking-python}}"
VERSION="${VERSION:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check environment variables
    local required_vars=("OPENAI_API_KEY" "GHL_API_KEY" "GHL_LOCATION_ID" "GHL_WEBHOOK_SECRET")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log_info "All requirements satisfied"
}

build_docker_image() {
    log_info "Building Docker image..."
    
    docker build \
        --build-arg VERSION="${VERSION}" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        -t "${DOCKER_IMAGE}:${VERSION}" \
        -t "${DOCKER_IMAGE}:latest" \
        .
    
    log_info "Docker image built successfully"
}

push_docker_image() {
    log_info "Pushing Docker image to registry..."
    
    # Login to registry if credentials provided
    if [ -n "${DOCKER_USERNAME:-}" ] && [ -n "${DOCKER_PASSWORD:-}" ]; then
        echo "${DOCKER_PASSWORD}" | docker login "${DOCKER_REGISTRY}" -u "${DOCKER_USERNAME}" --password-stdin
    fi
    
    docker push "${DOCKER_IMAGE}:${VERSION}"
    docker push "${DOCKER_IMAGE}:latest"
    
    log_info "Docker image pushed successfully"
}

deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Create .env file from environment
    cat > .env.production <<EOF
OPENAI_API_KEY=${OPENAI_API_KEY}
GHL_API_KEY=${GHL_API_KEY}
GHL_LOCATION_ID=${GHL_LOCATION_ID}
GHL_WEBHOOK_SECRET=${GHL_WEBHOOK_SECRET}
LANGSMITH_API_KEY=${LANGSMITH_API_KEY:-}
LANGSMITH_TRACING=${LANGSMITH_TRACING:-true}
LANGSMITH_PROJECT=${LANGSMITH_PROJECT:-ghl-booking-production}
REDIS_PASSWORD=${REDIS_PASSWORD:-$(openssl rand -base64 32)}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}
NODE_ENV=production
LOG_LEVEL=${LOG_LEVEL:-INFO}
EOF
    
    # Deploy with docker-compose
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    log_info "Docker Compose deployment complete"
}

deploy_cloud_run() {
    log_info "Deploying to Google Cloud Run..."
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is required for Cloud Run deployment"
        exit 1
    fi
    
    # Deploy to Cloud Run
    gcloud run deploy ${PROJECT_NAME} \
        --image "${DOCKER_IMAGE}:${VERSION}" \
        --platform managed \
        --region ${GCP_REGION:-us-central1} \
        --allow-unauthenticated \
        --set-env-vars NODE_ENV=production,LOG_LEVEL=${LOG_LEVEL:-INFO} \
        --set-secrets "OPENAI_API_KEY=openai-api-key:latest,GHL_API_KEY=ghl-api-key:latest,GHL_LOCATION_ID=ghl-location-id:latest,GHL_WEBHOOK_SECRET=ghl-webhook-secret:latest" \
        --memory 512Mi \
        --cpu 1 \
        --timeout 300 \
        --max-instances 10
    
    log_info "Cloud Run deployment complete"
}

deploy_aws_ecs() {
    log_info "Deploying to AWS ECS..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is required for ECS deployment"
        exit 1
    fi
    
    # Update task definition
    aws ecs register-task-definition \
        --family ${PROJECT_NAME} \
        --task-role-arn ${ECS_TASK_ROLE_ARN} \
        --execution-role-arn ${ECS_EXECUTION_ROLE_ARN} \
        --network-mode awsvpc \
        --requires-compatibilities FARGATE \
        --cpu 256 \
        --memory 512 \
        --container-definitions "[
            {
                \"name\": \"${PROJECT_NAME}\",
                \"image\": \"${DOCKER_IMAGE}:${VERSION}\",
                \"portMappings\": [{\"containerPort\": 8000}],
                \"environment\": [
                    {\"name\": \"NODE_ENV\", \"value\": \"production\"},
                    {\"name\": \"LOG_LEVEL\", \"value\": \"${LOG_LEVEL:-INFO}\"}
                ],
                \"secrets\": [
                    {\"name\": \"OPENAI_API_KEY\", \"valueFrom\": \"${OPENAI_SECRET_ARN}\"},
                    {\"name\": \"GHL_API_KEY\", \"valueFrom\": \"${GHL_API_SECRET_ARN}\"},
                    {\"name\": \"GHL_LOCATION_ID\", \"valueFrom\": \"${GHL_LOCATION_SECRET_ARN}\"},
                    {\"name\": \"GHL_WEBHOOK_SECRET\", \"valueFrom\": \"${GHL_WEBHOOK_SECRET_ARN}\"}
                ],
                \"logConfiguration\": {
                    \"logDriver\": \"awslogs\",
                    \"options\": {
                        \"awslogs-group\": \"/ecs/${PROJECT_NAME}\",
                        \"awslogs-region\": \"${AWS_REGION:-us-east-1}\",
                        \"awslogs-stream-prefix\": \"ecs\"
                    }
                }
            }
        ]"
    
    # Update service
    aws ecs update-service \
        --cluster ${ECS_CLUSTER_NAME} \
        --service ${PROJECT_NAME} \
        --task-definition ${PROJECT_NAME}
    
    log_info "AWS ECS deployment complete"
}

deploy_railway() {
    log_info "Deploying to Railway..."
    
    # Check Railway CLI
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI is required for Railway deployment"
        exit 1
    fi
    
    # Deploy to Railway
    railway up --service ${PROJECT_NAME}
    
    log_info "Railway deployment complete"
}

health_check() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    log_info "Running health check on ${url}..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "${url}/health" > /dev/null; then
            log_info "Health check passed!"
            return 0
        fi
        
        log_warn "Health check attempt ${attempt}/${max_attempts} failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health check failed after ${max_attempts} attempts"
    return 1
}

# Main deployment logic
main() {
    log_info "Starting deployment of ${PROJECT_NAME} (${VERSION}) to ${ENVIRONMENT}"
    
    # Check requirements
    check_requirements
    
    # Parse deployment target
    DEPLOY_TARGET="${1:-docker-compose}"
    
    # Build Docker image
    build_docker_image
    
    # Deploy based on target
    case "${DEPLOY_TARGET}" in
        "docker-compose")
            deploy_docker_compose
            health_check "http://localhost:8000"
            ;;
        "cloud-run")
            push_docker_image
            deploy_cloud_run
            SERVICE_URL=$(gcloud run services describe ${PROJECT_NAME} --platform managed --region ${GCP_REGION:-us-central1} --format 'value(status.url)')
            health_check "${SERVICE_URL}"
            ;;
        "aws-ecs")
            push_docker_image
            deploy_aws_ecs
            # Health check handled by ECS/ALB
            ;;
        "railway")
            push_docker_image
            deploy_railway
            # Railway provides automatic health checks
            ;;
        *)
            log_error "Unknown deployment target: ${DEPLOY_TARGET}"
            echo "Usage: $0 [docker-compose|cloud-run|aws-ecs|railway]"
            exit 1
            ;;
    esac
    
    log_info "Deployment completed successfully!"
}

# Run main function
main "$@"