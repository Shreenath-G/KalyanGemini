"""Bidding data models for real-time programmatic bidding"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class BidRequestStatus(str, Enum):
    """Status of bid request"""
    PENDING = "pending"
    EVALUATED = "evaluated"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"
    REJECTED = "rejected"


class UserProfile(BaseModel):
    """User profile data from ad exchange"""
    user_id: str = Field(..., description="Anonymous user identifier")
    demographics: Dict[str, Any] = Field(default_factory=dict, description="Demographic data")
    interests: List[str] = Field(default_factory=list, description="User interests")
    behaviors: List[str] = Field(default_factory=list, description="User behaviors")
    device_type: Optional[str] = Field(None, description="Device type (mobile, desktop, tablet)")
    location: Optional[Dict[str, str]] = Field(None, description="Geographic location")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "anon_user_12345",
                "demographics": {"age_range": "30-45", "gender": "all"},
                "interests": ["business", "technology", "productivity"],
                "behaviors": ["online_shopping", "software_usage"],
                "device_type": "desktop",
                "location": {"country": "US", "region": "CA"}
            }
        }


class AdInventory(BaseModel):
    """Ad inventory details from exchange"""
    inventory_id: str = Field(..., description="Inventory identifier")
    platform: str = Field(..., description="Ad platform (google, meta, programmatic)")
    placement_type: str = Field(..., description="Placement type (banner, video, native)")
    dimensions: Optional[Dict[str, int]] = Field(None, description="Ad dimensions")
    floor_price: float = Field(..., description="Minimum bid price", ge=0.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "inventory_id": "inv_67890",
                "platform": "programmatic",
                "placement_type": "banner",
                "dimensions": {"width": 728, "height": 90},
                "floor_price": 0.50
            }
        }


class BidRequest(BaseModel):
    """Bid request from ad exchange"""
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    user_profile: UserProfile = Field(..., description="User profile data")
    inventory: AdInventory = Field(..., description="Ad inventory details")
    timeout_ms: int = Field(default=100, description="Response timeout in milliseconds", ge=50, le=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123",
                "timestamp": "2024-01-15T10:30:00Z",
                "user_profile": {
                    "user_id": "anon_user_12345",
                    "demographics": {"age_range": "30-45"},
                    "interests": ["business", "technology"],
                    "behaviors": ["online_shopping"],
                    "device_type": "desktop"
                },
                "inventory": {
                    "inventory_id": "inv_67890",
                    "platform": "programmatic",
                    "placement_type": "banner",
                    "floor_price": 0.50
                },
                "timeout_ms": 100
            }
        }


class BidResponse(BaseModel):
    """Bid response to ad exchange"""
    request_id: str = Field(..., description="Original request identifier")
    bid_price: float = Field(..., description="Bid price in USD", ge=0.0)
    campaign_id: str = Field(..., description="Campaign identifier")
    creative_id: str = Field(..., description="Creative variant identifier")
    segment_id: str = Field(..., description="Audience segment identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123",
                "bid_price": 2.50,
                "campaign_id": "camp_001",
                "creative_id": "var_001",
                "segment_id": "seg_001",
                "timestamp": "2024-01-15T10:30:00.050Z"
            }
        }


class NoBidResponse(BaseModel):
    """No-bid response when not bidding on inventory"""
    request_id: str = Field(..., description="Original request identifier")
    reason: str = Field(..., description="Reason for not bidding")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123",
                "reason": "No matching segments",
                "timestamp": "2024-01-15T10:30:00.050Z"
            }
        }


class BidDecision(BaseModel):
    """Internal bid decision record"""
    request_id: str = Field(..., description="Request identifier")
    campaign_id: Optional[str] = Field(None, description="Campaign identifier")
    segment_id: Optional[str] = Field(None, description="Segment identifier")
    creative_id: Optional[str] = Field(None, description="Creative identifier")
    bid_price: Optional[float] = Field(None, description="Bid price submitted")
    decision: str = Field(..., description="Decision (bid, no_bid)")
    reason: str = Field(..., description="Decision reason")
    status: BidRequestStatus = Field(default=BidRequestStatus.PENDING, description="Bid status")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Decision timestamp")
    
    # Performance tracking
    user_conversion_probability: Optional[float] = Field(None, description="Estimated conversion probability")
    segment_max_cpc: Optional[float] = Field(None, description="Segment max CPC")
    budget_remaining_percent: Optional[float] = Field(None, description="Remaining budget percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123",
                "campaign_id": "camp_001",
                "segment_id": "seg_001",
                "creative_id": "var_001",
                "bid_price": 2.50,
                "decision": "bid",
                "reason": "High conversion probability match",
                "status": "submitted",
                "processing_time_ms": 45.2,
                "timestamp": "2024-01-15T10:30:00.050Z",
                "user_conversion_probability": 0.15,
                "segment_max_cpc": 3.00,
                "budget_remaining_percent": 65.0
            }
        }


class SegmentMatch(BaseModel):
    """Matched audience segment for a bid request"""
    campaign_id: str = Field(..., description="Campaign identifier")
    segment_id: str = Field(..., description="Segment identifier")
    creative_id: str = Field(..., description="Creative variant identifier")
    max_cpc: float = Field(..., description="Maximum CPC for this segment")
    match_score: float = Field(..., description="Match quality score", ge=0.0, le=1.0)
    conversion_probability: float = Field(..., description="Estimated conversion probability", ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "segment_id": "seg_001",
                "creative_id": "var_001",
                "max_cpc": 3.00,
                "match_score": 0.85,
                "conversion_probability": 0.15
            }
        }


class BudgetCheck(BaseModel):
    """Budget availability check result"""
    campaign_id: str = Field(..., description="Campaign identifier")
    available: bool = Field(..., description="Whether budget is available")
    remaining: float = Field(..., description="Remaining budget amount")
    remaining_percent: float = Field(..., description="Remaining budget percentage")
    daily_budget: float = Field(..., description="Daily budget amount")
    current_spend: float = Field(..., description="Current spend today")
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "available": True,
                "remaining": 65.50,
                "remaining_percent": 65.0,
                "daily_budget": 100.00,
                "current_spend": 34.50
            }
        }


class BiddingStrategy(BaseModel):
    """Bidding strategy configuration for a campaign"""
    campaign_id: str = Field(..., description="Campaign identifier")
    target_win_rate: float = Field(default=0.30, description="Target win rate (20-40%)", ge=0.20, le=0.40)
    current_win_rate: float = Field(default=0.0, description="Current win rate")
    bid_adjustment_factor: float = Field(default=1.0, description="Bid adjustment multiplier", ge=0.5, le=2.0)
    total_bids: int = Field(default=0, description="Total bids submitted")
    total_wins: int = Field(default=0, description="Total bids won")
    total_losses: int = Field(default=0, description="Total bids lost")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def update_win_rate(self) -> None:
        """Calculate current win rate"""
        if self.total_bids > 0:
            self.current_win_rate = self.total_wins / self.total_bids
        else:
            self.current_win_rate = 0.0
    
    def should_adjust_strategy(self) -> bool:
        """Check if strategy needs adjustment (after 100 bids)"""
        return self.total_bids >= 100 and self.total_bids % 100 == 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "target_win_rate": 0.30,
                "current_win_rate": 0.25,
                "bid_adjustment_factor": 1.05,
                "total_bids": 250,
                "total_wins": 62,
                "total_losses": 188,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }
