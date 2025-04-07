# Exercise 2: Deployment and Scaling

## Objective
In this exercise, you will learn about deploying and scaling the Testus Patronus application in Azure, focusing on best practices for production deployment.

## Tasks

### Task 1: Containerization
1. Create a Dockerfile for the backend
2. Create a Dockerfile for the frontend
3. Set up Docker Compose for local development
4. Test the containerized application

### Task 2: Azure Infrastructure
1. Create an Azure Resource Manager (ARM) template
2. Deploy the infrastructure using Azure CLI
3. Configure networking and security
4. Set up monitoring and logging

### Task 3: CI/CD Pipeline
1. Create a GitHub Actions workflow
2. Implement automated testing
3. Set up deployment stages (dev, staging, prod)
4. Configure environment-specific settings

### Task 4: Scaling and Performance
1. Implement caching for the vector store
2. Set up auto-scaling rules
3. Configure load balancing
4. Implement health checks

### Task 5: Security and Compliance
1. Implement Azure Key Vault integration
2. Set up managed identities
3. Configure network security rules
4. Implement audit logging

## Hints

### Task 1 Hint
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 2 Hint
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "location": {
      "type": "string",
      "defaultValue": "[resourceGroup().location]"
    }
  },
  "resources": [
    {
      "type": "Microsoft.Web/sites",
      "apiVersion": "2021-02-01",
      "name": "[parameters('webAppName')]",
      "location": "[parameters('location')]",
      "properties": {
        "serverFarmId": "[resourceId('Microsoft.Web/serverfarms', parameters('appServicePlanName'))]"
      }
    }
  ]
}
```

### Task 3 Hint
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
    - name: Run tests
      run: |
        pytest backend/tests
```

### Task 4 Hint
```python
# Example of implementing caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str) -> List[float]:
    return embeddings.embed_query(text)
```

### Task 5 Hint
```python
# Example of Key Vault integration
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)
secret = client.get_secret("openai-api-key")
```

## Evaluation Criteria

1. **Infrastructure as Code**
   - Well-structured ARM templates
   - Proper parameterization
   - Documentation of resources

2. **CI/CD Implementation**
   - Automated testing
   - Deployment stages
   - Environment configuration

3. **Security**
   - Proper secret management
   - Network security
   - Access control

4. **Scalability**
   - Efficient resource utilization
   - Proper scaling rules
   - Performance optimization

## Submission

1. Create a new branch for your work
2. Document your infrastructure setup
3. Provide deployment instructions
4. Include monitoring dashboards
5. Document security measures

## Bonus Challenges

1. Implement blue-green deployment
2. Set up disaster recovery
3. Create a cost optimization strategy
4. Implement A/B testing infrastructure

## Resources

- [Azure Container Registry Documentation](https://docs.microsoft.com/en-us/azure/container-registry/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [Azure Monitor Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/)

## Tips for Success

1. **Start Small**
   - Begin with basic containerization
   - Add complexity gradually
   - Test each component thoroughly

2. **Security First**
   - Never commit secrets
   - Use managed identities
   - Implement least privilege access

3. **Monitor Everything**
   - Set up logging early
   - Create dashboards
   - Configure alerts

4. **Documentation**
   - Document all infrastructure
   - Create runbooks
   - Maintain deployment guides

## Common Pitfalls

1. **Security**
   - Exposed secrets
   - Missing network security
   - Inadequate access control

2. **Performance**
   - Insufficient resources
   - Missing caching
   - Poor scaling configuration

3. **Maintenance**
   - Lack of monitoring
   - Missing backup strategy
   - Poor documentation

## Next Steps

1. Review Azure best practices
2. Implement monitoring
3. Set up alerts
4. Create maintenance procedures
5. Document operational procedures 