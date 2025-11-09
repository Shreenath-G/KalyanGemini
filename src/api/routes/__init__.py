"""API routes package"""

from src.api.routes.campaigns import router as campaigns_router
from src.api.routes.performance import router as performance_router
from src.api.routes.bidding import router as bidding_router
from src.api.routes.data_export import router as data_export_router

__all__ = ["campaigns_router", "performance_router", "bidding_router", "data_export_router"]
