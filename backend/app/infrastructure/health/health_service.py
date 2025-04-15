from typing import Dict
from app.infrastructure.health.vector_store_checker import VectorStoreHealthChecker
from app.infrastructure.health.openai_checker import OpenAIHealthChecker

class HealthService:
    def __init__(self):
        self.checkers = [
            VectorStoreHealthChecker(),
            OpenAIHealthChecker()
        ]

    async def check_services(self) -> Dict[str, str]:
        results = {"api": "operational"}
        for checker in self.checkers:
            results[checker.service_name] = await checker.check_health()
        return results 