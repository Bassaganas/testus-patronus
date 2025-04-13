from fastapi import HTTPException
from typing import Any, Dict, Optional

class APIError(HTTPException):
    """Base API error class"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=404,
            detail=f"{resource} not found with ID: {resource_id}"
        )

class ValidationError(APIError):
    """Validation error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=400,
            detail=detail
        )

class ServiceError(APIError):
    """External service error"""
    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=503,
            detail=f"{service} service error: {detail}"
        ) 