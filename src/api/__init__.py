"""API package for Adaptive Ad Intelligence Platform"""

from src.api.routes import campaigns_router, performance_router
from src.api.middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    AuthenticationMiddleware
)
from src.api.errors import (
    APIError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    AgentTimeoutError,
    AgentError
)

__all__ = [
    "campaigns_router",
    "performance_router",
    "ErrorHandlingMiddleware",
    "RequestLoggingMiddleware",
    "AuthenticationMiddleware",
    "APIError",
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "AgentTimeoutError",
    "AgentError"
]
