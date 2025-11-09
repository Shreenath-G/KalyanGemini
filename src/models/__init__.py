"""Data models package"""

from src.models.campaign import (
    Campaign,
    CampaignRequest,
    CampaignResponse,
    CampaignStatus,
    OptimizationMode
)
from src.models.creative import (
    CreativeVariant,
    CreativeHeadlines,
    CreativeStatus
)
from src.models.audience import (
    AudienceSegment,
    Demographics,
    SegmentSize
)
from src.models.budget import (
    BudgetAllocation,
    SegmentAllocation,
    PlatformSplit
)
from src.models.metrics import (
    PerformanceMetrics,
    VariantMetrics,
    SegmentMetrics,
    PlatformMetrics,
    MetricsSnapshot
)
from src.models.bidding import (
    BidRequest,
    BidResponse,
    NoBidResponse,
    BidDecision,
    SegmentMatch,
    BudgetCheck,
    BiddingStrategy,
    BidRequestStatus,
    UserProfile,
    AdInventory
)

__all__ = [
    # Campaign models
    "Campaign",
    "CampaignRequest",
    "CampaignResponse",
    "CampaignStatus",
    "OptimizationMode",
    # Creative models
    "CreativeVariant",
    "CreativeHeadlines",
    "CreativeStatus",
    # Audience models
    "AudienceSegment",
    "Demographics",
    "SegmentSize",
    # Budget models
    "BudgetAllocation",
    "SegmentAllocation",
    "PlatformSplit",
    # Metrics models
    "PerformanceMetrics",
    "VariantMetrics",
    "SegmentMetrics",
    "PlatformMetrics",
    "MetricsSnapshot",
    # Bidding models
    "BidRequest",
    "BidResponse",
    "NoBidResponse",
    "BidDecision",
    "SegmentMatch",
    "BudgetCheck",
    "BiddingStrategy",
    "BidRequestStatus",
    "UserProfile",
    "AdInventory",
]
