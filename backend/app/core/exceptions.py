from fastapi import HTTPException

class NotFoundException(HTTPException):
    """
    Exception raised when a resource is not found
    """
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)

class ValidationException(HTTPException):
    """
    Exception raised when validation fails
    """
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class UnauthorizedException(HTTPException):
    """
    Exception raised when user is not authorized
    """
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=401, detail=detail)

class ForbiddenException(HTTPException):
    """
    Exception raised when user is forbidden
    """
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)

class ConflictException(HTTPException):
    """
    Exception raised when there is a conflict
    """
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail)

class InternalServerException(HTTPException):
    """
    Exception raised when there is an internal server error
    """
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=500, detail=detail) 