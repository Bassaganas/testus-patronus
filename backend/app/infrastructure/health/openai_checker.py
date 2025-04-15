import httpx
from app.core.config import settings

class OpenAIHealthChecker:
    service_name = "openai"

    async def check_health(self) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments",
                    headers={
                        "api-key": settings.AZURE_OPENAI_API_KEY,
                        "api-version": settings.AZURE_OPENAI_API_VERSION
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    return "operational"
                return "degraded"
        except Exception:
            return "error" 