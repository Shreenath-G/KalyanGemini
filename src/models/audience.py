"""Audience segment data models"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class SegmentSize(str, Enum):
    """Audience segment size enumeration"""
    SMALL = "small"      # < 100,000 users
    MEDIUM = "medium"    # 100,000 - 1,000,000 users
    LARGE = "large"      # > 1,000,000 users


class Demographics(BaseModel):
    """Demographic targeting criteria"""
    
    age_range: str = Field(..., description="Age range (e.g., '30-50')")
    gender: str = Field(default="all", description="Gender targeting")
    income: Optional[str] = Field(default=None, description="Income range")
    
    @field_validator('age_range')
    @classmethod
    def validate_age_range(cls, v: str) -> str:
        """Validate age range format"""
        if not v.strip():
            raise ValueError("Age range cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "age_range": "30-50",
                "gender": "all",
                "income": "50k-150k"
            }
        }


class AudienceSegment(BaseModel):
    """Audience segment data model with validation"""
    
    # Identifiers
    segment_id: str = Field(..., description="Unique segment identifier")
    campaign_id: str = Field(..., description="Associated campaign ID")
    name: str = Field(..., min_length=1, max_length=200, description="Segment name")
    
    # Targeting criteria
    demographics: Demographics = Field(..., description="Demographic criteria")
    interests: List[str] = Field(..., min_length=1, description="Interest categories")
    behaviors: List[str] = Field(default_factory=list, description="Behavioral patterns")
    
    # Estimates
    estimated_size: SegmentSize = Field(..., description="Estimated audience size")
    conversion_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted conversion probability")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Priority ranking score")
    
    # Performance metrics
    impressions: int = Field(default=0, ge=0, description="Total impressions")
    clicks: int = Field(default=0, ge=0, description="Total clicks")
    conversions: int = Field(default=0, ge=0, description="Total conversions")
    spend: float = Field(default=0.0, ge=0.0, description="Total spend")
    roas: float = Field(default=0.0, ge=0.0, description="Return on ad spend")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v: List[str]) -> List[str]:
        """Validate interests list"""
        if not v:
            raise ValueError("At least one interest must be specified")
        for interest in v:
            if not interest.strip():
                raise ValueError("Interest cannot be empty")
        return [i.strip() for i in v]
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate segment name"""
        if not v.strip():
            raise ValueError("Segment name cannot be empty")
        return v.strip()
    
    def calculate_ctr(self) -> float:
        """Calculate click-through rate"""
        if self.impressions == 0:
            return 0.0
        return (self.clicks / self.impressions) * 100
    
    def calculate_conversion_rate(self) -> float:
        """Calculate conversion rate"""
        if self.clicks == 0:
            return 0.0
        return (self.conversions / self.clicks) * 100
    
    def calculate_cpa(self) -> float:
        """Calculate cost per acquisition"""
        if self.conversions == 0:
            return 0.0
        return self.spend / self.conversions
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment_id": "seg_001",
                "campaign_id": "camp_001",
                "name": "Tech-Savvy Small Business Owners",
                "demographics": {
                    "age_range": "30-50",
                    "gender": "all",
                    "income": "50k-150k"
                },
                "interests": ["entrepreneurship", "technology", "productivity"],
                "behaviors": ["online shopping", "business software usage"],
                "estimated_size": "medium",
                "conversion_probability": 0.12,
                "priority_score": 0.85,
                "impressions": 25000,
                "clicks": 1250,
                "conversions": 62,
                "spend": 625.0,
                "roas": 3.5
            }
        }
