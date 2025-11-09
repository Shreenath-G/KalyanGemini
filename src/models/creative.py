"""Creative variant data models"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional
from datetime import datetime
from enum import Enum


class CreativeStatus(str, Enum):
    """Creative variant status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    TESTING = "testing"


class CreativeHeadlines(BaseModel):
    """Headlines for different character limits"""
    
    short: str = Field(..., max_length=30, description="Short headline (30 chars)")
    medium: str = Field(..., max_length=60, description="Medium headline (60 chars)")
    long: str = Field(..., max_length=90, description="Long headline (90 chars)")
    
    @field_validator('short', 'medium', 'long')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure headlines are not empty"""
        if not v.strip():
            raise ValueError("Headline cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "short": "Save 50% Today",
                "medium": "Limited Time: Save 50% on Premium Plans",
                "long": "Don't Miss Out: Save 50% on All Premium Plans This Week Only"
            }
        }


class CreativeVariant(BaseModel):
    """Creative variant data model with validation"""
    
    # Identifiers
    variant_id: str = Field(..., description="Unique variant identifier")
    campaign_id: str = Field(..., description="Associated campaign ID")
    status: CreativeStatus = Field(default=CreativeStatus.TESTING, description="Variant status")
    
    # Content
    headlines: CreativeHeadlines = Field(..., description="Headlines for different platforms")
    body: str = Field(..., max_length=150, description="Body copy")
    cta: str = Field(..., max_length=20, description="Call-to-action text")
    
    # Performance metrics
    impressions: int = Field(default=0, ge=0, description="Total impressions")
    clicks: int = Field(default=0, ge=0, description="Total clicks")
    conversions: int = Field(default=0, ge=0, description="Total conversions")
    spend: float = Field(default=0.0, ge=0.0, description="Total spend")
    roas: float = Field(default=0.0, ge=0.0, description="Return on ad spend")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    compliance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Compliance score")
    
    @field_validator('body')
    @classmethod
    def validate_body(cls, v: str) -> str:
        """Validate body copy"""
        if not v.strip():
            raise ValueError("Body copy cannot be empty")
        return v.strip()
    
    @field_validator('cta')
    @classmethod
    def validate_cta(cls, v: str) -> str:
        """Validate call-to-action"""
        if not v.strip():
            raise ValueError("Call-to-action cannot be empty")
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
                "variant_id": "var_001",
                "campaign_id": "camp_001",
                "status": "active",
                "headlines": {
                    "short": "Save 50% Today",
                    "medium": "Limited Time: Save 50% on Premium Plans",
                    "long": "Don't Miss Out: Save 50% on All Premium Plans This Week Only"
                },
                "body": "Upgrade your business with our premium features. Easy setup, no contracts, cancel anytime.",
                "cta": "Get Started Now",
                "impressions": 10000,
                "clicks": 500,
                "conversions": 25,
                "spend": 250.0,
                "roas": 3.2,
                "compliance_score": 0.95
            }
        }
