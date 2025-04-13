# Deployment Guide for Testus Patronus

This guide will walk you through deploying both the backend and frontend components of Testus Patronus.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)
- Access to Azure OpenAI or OpenAI API credentials

## Setup

1. Clone the repository (if you haven't already):
   ```bash
   git clone <your-repository-url>
   cd testus-patronus
   ```

2. Configure the backend environment variables:
   - Edit `backend/.env` with your Azure OpenAI or OpenAI API credentials
   - Adjust other settings as needed

## Local Deployment with Docker Compose

1. Build and start the services:
   ```bash
   docker-compose up -d
   ```

2. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

3. To stop the services:
   ```bash
   docker-compose down
   ```

## Cloud Deployment

### Azure Deployment

#### Azure Container Apps

1. Create an Azure Container Registry (ACR):
   ```bash
   az acr create --resource-group myResourceGroup --name myContainerRegistry --sku Basic
   ```

2. Build and push the Docker images:
   ```bash
   # Login to ACR
   az acr login --name myContainerRegistry
   
   # Tag the images
   docker tag testus-patronus-backend mycontainerregistry.azurecr.io/testus-patronus-backend:latest
   docker tag testus-patronus-frontend mycontainerregistry.azurecr.io/testus-patronus-frontend:latest
   
   # Push the images
   docker push mycontainerregistry.azurecr.io/testus-patronus-backend:latest
   docker push mycontainerregistry.azurecr.io/testus-patronus-frontend:latest
   ```

3. Deploy to Azure Container Apps:
   ```bash
   # Create Container App Environment
   az containerapp env create --name myEnvironment --resource-group myResourceGroup --location eastus
   
   # Deploy backend
   az containerapp create --name testus-patronus-backend \
     --resource-group myResourceGroup \
     --environment myEnvironment \
     --image mycontainerregistry.azurecr.io/testus-patronus-backend:latest \
     --target-port 8000 \
     --ingress external
   
   # Deploy frontend
   az containerapp create --name testus-patronus-frontend \
     --resource-group myResourceGroup \
     --environment myEnvironment \
     --image mycontainerregistry.azurecr.io/testus-patronus-frontend:latest \
     --target-port 80 \
     --ingress external
   ```

### AWS Deployment

#### Amazon ECS

1. Create an ECR repository:
   ```bash
   aws ecr create-repository --repository-name testus-patronus-backend
   aws ecr create-repository --repository-name testus-patronus-frontend
   ```

2. Build and push the Docker images:
   ```bash
   # Get login credentials for ECR
   aws ecr get-login-password | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com
   
   # Tag the images
   docker tag testus-patronus-backend <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com/testus-patronus-backend:latest
   docker tag testus-patronus-frontend <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com/testus-patronus-frontend:latest
   
   # Push the images
   docker push <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com/testus-patronus-backend:latest
   docker push <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com/testus-patronus-frontend:latest
   ```

3. Create ECS cluster and task definitions, then deploy services (this can be done through the AWS Management Console or CLI)

## Data Persistence

For production environments, consider setting up:

1. A persistent volume for vector store data
2. A database for storing conversations and documents metadata (e.g., PostgreSQL)

## Security Considerations

1. Always use HTTPS in production
2. Secure your API keys and credentials
3. Set up proper authentication for your application
4. Configure CORS settings appropriately

## Monitoring and Logging

1. Set up logging for both frontend and backend
2. Consider using services like:
   - Azure Application Insights
   - AWS CloudWatch
   - Datadog
   - Prometheus and Grafana

## Troubleshooting

- Check logs: `docker-compose logs -f`
- Verify network connectivity between services
- Ensure environment variables are correctly set
- Check that volumes are properly mounted 