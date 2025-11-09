"""API error handling and custom exceptions"""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class APIError(HTTPException):
    """Base API error class"""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.retry_after = retry_after
        
        content = {
            "error": {
                "code": error_code,
                "message": message
            }
        }
        
        if details:
            content["error"]["details"] = details
        
        if retry_after:
            content["error"]["retry_after"] = retry_after
        
        super().__init__(status_code=status_code, detail=content)


class ValidationError(APIError):
    """Validation error"""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details
        )


class AuthenticationError(APIError):
    """Authentication error"""
    
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            message=message
        )


class RateLimitError(APIError):
    """Rate limit exceeded error"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded",
            details="You have exceeded the maximum number of requests per minute",
            retry_after=retry_after
        )


class NotFoundError(APIError):
    """Resource not found error"""
    
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=f"{resource} not found",
            details=f"No {resource} found with ID: {resource_id}"
        )


class AgentTimeoutError(APIError):
    """Agent timeout error"""
    
    def __init__(self, agent_name: str, fallback_applied: bool = False):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="AGENT_TIMEOUT",
            message=f"{agent_name} timed out",
            details=f"The {agent_name} did not respond within the expected time. " +
                   ("Fallback strategy was applied." if fallback_applied else "Please try again."),
            retry_after=60
        )


class AgentError(APIError):
    """Agent processing error"""
    
    def __init__(self, agent_name: str, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="AGENT_ERROR",
            message=f"{agent_name} error",
            details=message
        )


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[str] = None,
    retry_after: Optional[int] = None
) -> Dict[str, Any]:
    """Create a standardized error response"""
    response = {
        "error": {
            "code": error_code,
            "message": message
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if retry_after:
        response["error"]["retry_after"] = retry_after
    
    return response
