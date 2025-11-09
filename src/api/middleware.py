"""API middleware components"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import uuid
from typing import Callable

from src.api.errors import AuthenticationError, RateLimitError
from src.api.auth import verify_api_key
from src.api.rate_limit import check_rate_limit
from src.utils.logging_config import set_correlation_id, clear_correlation_id
from src.utils.metrics import track_api_request

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and exceptions"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except ValueError as exc:
            logger.warning(f"Validation error: {exc}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(exc),
                        "details": "Request validation failed"
                    }
                }
            )
        except Exception as exc:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": str(exc) if request.app.state.settings.environment == "development" else None
                    }
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses with correlation IDs
    
    Requirements: 12.1, 12.5
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Set correlation ID in context for all subsequent logs
        set_correlation_id(correlation_id)
        
        # Store in request state for access by routes
        request.state.correlation_id = correlation_id
        
        # Log request with correlation ID
        logger.info(
            f"Request started",
            extra={
                "event_type": "request_started",
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
                "correlation_id": correlation_id,
                "user_agent": request.headers.get("User-Agent"),
                "query_params": dict(request.query_params)
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Track metrics
            track_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "event_type": "request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_seconds": round(duration, 3),
                    "correlation_id": correlation_id
                }
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(round(duration, 3))
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Log error with correlation ID
            duration = time.time() - start_time
            
            # Track error metrics
            track_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=duration
            )
            
            logger.error(
                f"Request failed",
                extra={
                    "event_type": "request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_seconds": round(duration, 3),
                    "correlation_id": correlation_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        
        finally:
            # Clear correlation ID from context
            clear_correlation_id()



class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication and rate limiting"""
    
    # Paths that don't require authentication
    PUBLIC_PATHS = ["/", "/docs", "/redoc", "/openapi.json", "/api/health"]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        try:
            # Get settings from app state or import directly
            from src.config import settings
            api_key_header = getattr(request.app.state, 'settings', settings).api_key_header
            
            # Extract and verify API key
            api_key = request.headers.get(api_key_header)
            
            if not api_key:
                raise AuthenticationError("API key is required")
            
            # Verify API key and get account ID
            # Simple validation for now
            if not api_key.startswith("sk_") or len(api_key) < 32:
                raise AuthenticationError("Invalid API key format")
            
            # Extract account ID from API key
            parts = api_key.split("_")
            if len(parts) < 3:
                raise AuthenticationError("Invalid API key")
            
            account_id = parts[1]
            
            # Store account ID in request state
            request.state.account_id = account_id
            
            # Check rate limit
            await check_rate_limit(request, account_id)
            
            # Log authenticated request
            logger.info(
                f"Authenticated request",
                extra={
                    "account_id": account_id,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            if hasattr(request.state, "rate_limit_remaining"):
                response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
                response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
            
            return response
            
        except (AuthenticationError, RateLimitError) as exc:
            # Return error response
            content = exc.detail if hasattr(exc, 'detail') else {
                "error": {
                    "code": exc.error_code,
                    "message": exc.message
                }
            }
            
            headers = {}
            if hasattr(exc, 'retry_after') and exc.retry_after:
                headers["Retry-After"] = str(exc.retry_after)
            
            return JSONResponse(
                status_code=exc.status_code,
                content=content,
                headers=headers
            )
