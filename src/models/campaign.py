"""Campaign data models"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CampaignStatus(str, Enum):
    """Campaign status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class OptimizationMode(str, Enum):
    """Optimization mode enumeration"""
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


class Campaign(BaseModel):
    """Campaign data model with validation"""
    
    # Identifiers
    campaign_id: str = Field(..., description="Unique campaign identifier")
    account_id: str = Field(..., description="Account identifier")
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, description="Campaign status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    # Input data
    business_goal: str = Field(..., min_length=1, max_length=500, description="Business objective")
    monthly_budget: float = Field(..., ge=100.0, le=100000.0, description="Monthly budget in USD")
    target_audience: str = Field(..., min_length=1, max_length=1000, description="Target audience description")
    products: List[str] = Field(..., min_length=1, description="List of products or services")
    
    # Generated strategy (optional, populated after agent processing)
    creative_variants: List[Dict[str, Any]] = Field(default_factory=list, description="Creative variations")
    audience_segments: List[Dict[str, Any]] = Field(default_factory=list, description="Audience segments")
    budget_allocation: Optional[Dict[str, Any]] = Field(default=None, description="Budget allocation plan")
    
    # Performance data
    total_spend: float = Field(default=0.0, ge=0.0, description="Total spend to date")
    total_impressions: int = Field(default=0, ge=0, description="Total impressions")
    total_clicks: int = Field(default=0, ge=0, description="Total clicks")
    total_conversions: int = Field(default=0, ge=0, description="Total conversions")
    current_roas: float = Field(default=0.0, ge=0.0, description="Current return on ad spend")
    
    # Metadata
    optimization_mode: OptimizationMode = Field(default=OptimizationMode.STANDARD, description="Optimization mode")
    last_optimized_at: Optional[datetime] = Field(default=None, description="Last optimization timestamp")
    
    @field_validator('products')
    @classmethod
    def validate_products(cls, v: List[str]) -> List[str]:
        """Validate products list"""
        if not v:
            raise ValueError("At least one product must be specified")
        # Ensure each product has content
        for product in v:
            if not product.strip():
                raise ValueError("Product descriptions cannot be empty")
        return v
    
    @model_validator(mode='after')
    def validate_budget_spend(self) -> 'Campaign':
        """Validate that spend doesn't exceed budget"""
        if self.total_spend > self.monthly_budget * 1.05:  # Allow 5% overspend
            raise ValueError(f"Total spend ({self.total_spend}) exceeds budget by more than 5%")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "account_id": "acc_123",
                "status": "active",
                "business_goal": "increase_signups",
                "monthly_budget": 5000.0,
                "target_audience": "small business owners aged 30-50",
                "products": ["CRM Software"],
                "total_spend": 1250.0,
                "total_impressions": 50000,
                "total_clicks": 2500,
                "total_conversions": 125,
                "current_roas": 3.2
            }
        }


class CampaignRequest(BaseModel):
    """Campaign creation request model"""
    
    business_goal: str = Field(..., min_length=1, max_length=500, description="Business objective")
    monthly_budget: float = Field(..., ge=100.0, le=100000.0, description="Monthly budget in USD")
    target_audience: str = Field(..., min_length=1, max_length=1000, description="Target audience description")
    products: List[str] = Field(..., min_length=1, description="List of products or services")
    optimization_mode: OptimizationMode = Field(default=OptimizationMode.STANDARD, description="Optimization mode")
    
    @field_validator('products')
    @classmethod
    def validate_products(cls, v: List[str]) -> List[str]:
        """Validate products list"""
        if not v:
            raise ValueError("At least one product must be specified")
        for product in v:
            if not product.strip():
                raise ValueError("Product descriptions cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "business_goal": "increase_signups",
                "monthly_budget": 5000.0,
                "target_audience": "small business owners aged 30-50",
                "products": ["CRM Software"],
                "optimization_mode": "standard"
            }
        }


class CampaignResponse(BaseModel):
    """Campaign creation response model"""
    
    campaign_id: str = Field(..., description="Unique campaign identifier")
    status: CampaignStatus = Field(..., description="Campaign status")
    estimated_launch: str = Field(..., description="Estimated launch timeline")
    message: str = Field(default="Campaign created successfully", description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "status": "draft",
                "estimated_launch": "24-48 hours",
                "message": "Campaign created successfully"
            }
        }
