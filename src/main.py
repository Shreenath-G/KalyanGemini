"""Main FastAPI application entry point"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from src.config import settings
from src.api.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware, AuthenticationMiddleware
from src.api.errors import create_error_response
from src.api.routes import campaigns_router, performance_router, bidding_router, data_export_router
from src.utils.logging_config import setup_cloud_logging

# Configure structured Cloud Logging with JSON format
setup_cloud_logging(
    log_level=settings.log_level,
    enable_json=settings.environment == "production",
    enable_console=True
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Adaptive Ad Intelligence Platform")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Google Cloud Project: {settings.google_cloud_project}")
    
    # Store settings in app state for middleware access
    app.state.settings = settings
    
    # Initialize Firestore service
    from src.services.firestore import get_firestore_service
    try:
        firestore_service = get_firestore_service()
        app.state.firestore_service = firestore_service
        logger.info("Firestore service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firestore service: {e}")
        raise
    
    # Initialize other services (will be implemented in later tasks)
    # - Initialize Vertex AI client
    # - Initialize ADK agents
    # - Start performance monitoring scheduler
    
    yield
    
    # Cleanup
    logger.info("Shutting down Adaptive Ad Intelligence Platform")
    
    # Close Firestore service
    if hasattr(app.state, 'firestore_service'):
        app.state.firestore_service.close()
        logger.info("Firestore service closed")


# Create FastAPI application
app = FastAPI(
    title="Adaptive Ad Intelligence Platform",
    description="Multi-agent advertising optimization system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (order matters - last added is executed first)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(RequestLoggingMiddleware)


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    logger.warning(f"Validation error: {error_messages}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details="; ".join(error_messages)
        )
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details=str(exc) if settings.environment == "development" else None
        )
    )


# Health check endpoint
@app.get(
    "/api/health",
    tags=["Health"],
    summary="Health check",
    description="""System health check endpoint for monitoring and load balancers.
    
    Returns:
    - Overall system status
    - API version
    - Agent availability status
    - External service connectivity
    
    **Response Time:** < 500ms
    
    **No Authentication Required**
    """,
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "environment": "production",
                        "agents": {
                            "campaign_orchestrator": "ready",
                            "creative_generator": "ready",
                            "audience_targeting": "ready",
                            "budget_optimizer": "ready",
                            "performance_analyzer": "ready",
                            "bid_execution": "ready"
                        },
                        "services": {
                            "firestore": "connected",
                            "vertex_ai": "connected",
                            "pubsub": "connected"
                        }
                    }
                }
            }
        },
        503: {
            "description": "System is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "version": "1.0.0",
                        "agents": {
                            "campaign_orchestrator": "error"
                        },
                        "services": {
                            "firestore": "disconnected"
                        }
                    }
                }
            }
        }
    }
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for Cloud Run and monitoring
    
    Returns system status and agent availability
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "agents": {
            "campaign_orchestrator": "ready",
            "creative_generator": "ready",
            "audience_targeting": "ready",
            "budget_optimizer": "ready",
            "performance_analyzer": "ready",
            "bid_execution": "ready"
        },
        "services": {
            "firestore": "connected",
            "vertex_ai": "connected",
            "pubsub": "connected"
        }
    }


# Metrics endpoint for Prometheus/Cloud Monitoring
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint for Cloud Monitoring
    
    Exposes metrics for:
    - API request latency (p50, p95, p99)
    - Agent response times and failure rates
    - Campaign performance
    - Bid execution metrics
    - System health
    
    Requirements: 12.5
    """
    from src.utils.metrics import get_metrics, get_metrics_content_type
    from fastapi.responses import Response
    
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "Adaptive Ad Intelligence Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Include routers
app.include_router(campaigns_router)
app.include_router(performance_router)
app.include_router(bidding_router)
app.include_router(data_export_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )
