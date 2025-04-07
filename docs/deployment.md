# Testus Patronus - Azure Deployment Guide

This guide will help you deploy the Testus Patronus application to Azure.

## Prerequisites

1. Azure subscription
2. Azure CLI installed
3. Docker installed (for local testing)
4. GitHub account

## Deployment Steps

### 1. Azure Resource Setup

1. Create a Resource Group:
   ```bash
   az group create --name testus-patronus-rg --location eastus
   ```

2. Create an Azure Container Registry:
   ```bash
   az acr create --resource-group testus-patronus-rg \
     --name testuspatronusacr --sku Basic
   ```

3. Create an Azure OpenAI resource:
   ```bash
   az cognitiveservices account create \
     --name testus-patronus-openai \
     --resource-group testus-patronus-rg \
     --location eastus \
     --kind OpenAI \
     --sku S0
   ```

4. Create an App Service Plan:
   ```bash
   az appservice plan create \
     --name testus-patronus-plan \
     --resource-group testus-patronus-rg \
     --location eastus \
     --sku B1 \
     --is-linux
   ```

### 2. Backend Deployment

1. Build and push the backend Docker image:
   ```bash
   cd backend
   docker build -t testuspatronusacr.azurecr.io/backend:latest .
   az acr login --name testuspatronusacr
   docker push testuspatronusacr.azurecr.io/backend:latest
   ```

2. Create the backend App Service:
   ```bash
   az webapp create \
     --resource-group testus-patronus-rg \
     --plan testus-patronus-plan \
     --name testus-patronus-backend \
     --deployment-container-image-name testuspatronusacr.azurecr.io/backend:latest
   ```

3. Configure environment variables:
   ```bash
   az webapp config appsettings set \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend \
     --settings \
     AZURE_OPENAI_API_KEY="your-api-key" \
     AZURE_OPENAI_ENDPOINT="your-endpoint" \
     AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
   ```

### 3. Frontend Deployment

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Create a storage account for static hosting:
   ```bash
   az storage account create \
     --name testuspatronusfrontend \
     --resource-group testus-patronus-rg \
     --location eastus \
     --sku Standard_LRS
   ```

3. Enable static website hosting:
   ```bash
   az storage blob service-properties update \
     --account-name testuspatronusfrontend \
     --static-website \
     --index-document index.html \
     --404-document index.html
   ```

4. Upload the frontend build:
   ```bash
   az storage blob upload-batch \
     --account-name testuspatronusfrontend \
     --auth-mode key \
     --source dist \
     --destination '$web' \
     --overwrite
   ```

### 4. Configure CORS and Networking

1. Update backend CORS settings:
   ```bash
   az webapp cors add \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend \
     --allowed-origins "https://testuspatronusfrontend.z13.web.core.windows.net"
   ```

2. Configure network rules:
   ```bash
   az webapp config set \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend \
     --linux-fx-version "DOCKER|testuspatronusacr.azurecr.io/backend:latest" \
     --always-on true
   ```

## Monitoring and Maintenance

1. Enable Application Insights:
   ```bash
   az webapp monitor application-insights component create \
     --app testus-patronus-backend \
     --location eastus \
     --resource-group testus-patronus-rg
   ```

2. Set up logging:
   ```bash
   az webapp log config \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend \
     --docker-container-logging filesystem
   ```

## Scaling and Performance

1. Configure auto-scaling:
   ```bash
   az monitor autoscale create \
     --resource-group testus-patronus-rg \
     --name testus-patronus-autoscale \
     --min-count 1 \
     --max-count 3 \
     --count 1
   ```

2. Add scaling rules:
   ```bash
   az monitor autoscale rule create \
     --resource-group testus-patronus-rg \
     --autoscale-name testus-patronus-autoscale \
     --condition "CPU Percentage > 70 avg 5m" \
     --scale up 1
   ```

## Backup and Recovery

1. Enable backup:
   ```bash
   az webapp config backup create \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend \
     --backup-name "daily-backup" \
     --storage-account-url "https://testuspatronusbackup.blob.core.windows.net" \
     --frequency "Daily" \
     --retention-days 7
   ```

## Cost Optimization

1. Set up budget alerts:
   ```bash
   az monitor activity-log alert create \
     --resource-group testus-patronus-rg \
     --name "cost-alert" \
     --condition category=Administrative \
     --action-group "/subscriptions/{subscription-id}/resourceGroups/testus-patronus-rg/providers/microsoft.insights/actionGroups/cost-alerts"
   ```

## Security Considerations

1. Enable HTTPS-only:
   ```bash
   az webapp update \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend \
     --https-only true
   ```

2. Configure managed identities:
   ```bash
   az webapp identity assign \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend
   ```

## Troubleshooting

1. Check application logs:
   ```bash
   az webapp log tail \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend
   ```

2. Restart the application:
   ```bash
   az webapp restart \
     --resource-group testus-patronus-rg \
     --name testus-patronus-backend
   ```

## Cleanup

To remove all resources:
```bash
az group delete --name testus-patronus-rg --yes
``` 