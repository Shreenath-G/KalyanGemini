"""Budget allocation data models"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict
from datetime import datetime


class PlatformSplit(BaseModel):
    """Budget split across advertising platforms"""
    
    google_ads: float = Field(..., ge=0.0, le=1.0, description="Google Ads allocation (0-1)")
    meta_ads: float = Field(..., ge=0.0, le=1.0, description="Meta Ads allocation (0-1)")
    programmatic: float = Field(..., ge=0.0, le=1.0, description="Programmatic allocation (0-1)")
    
    @model_validator(mode='after')
    def validate_total_allocation(self) -> 'PlatformSplit':
        """Ensure platform splits sum to 1.0"""
        total = self.google_ads + self.meta_ads + self.programmatic
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Platform splits must sum to 1.0, got {total}")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "google_ads": 0.40,
                "meta_ads": 0.40,
                "programmatic": 0.20
            }
        }


class SegmentAllocation(BaseModel):
    """Budget allocation for a specific audience segment"""
    
    segment_id: str = Field(..., description="Audience segment identifier")
    daily_budget: float = Field(..., gt=0.0, description="Daily budget allocation")
    platform_split: PlatformSplit = Field(..., description="Budget split across platforms")
    max_cpc: float = Field(..., gt=0.0, description="Maximum cost per click")
    current_spend: float = Field(default=0.0, ge=0.0, description="Current spend for this allocation")
    
    @field_validator('daily_budget')
    @classmethod
    def validate_daily_budget(cls, v: float) -> float:
        """Validate daily budget is positive"""
        if v <= 0:
            raise ValueError("Daily budget must be greater than 0")
        return v
    
    @field_validator('max_cpc')
    @classmethod
    def validate_max_cpc(cls, v: float) -> float:
        """Validate max CPC is positive"""
        if v <= 0:
            raise ValueError("Max CPC must be greater than 0")
        return v
    
    def get_platform_budget(self, platform: str) -> float:
        """Get daily budget for a specific platform"""
        platform_map = {
            "google_ads": self.platform_split.google_ads,
            "meta_ads": self.platform_split.meta_ads,
            "programmatic": self.platform_split.programmatic
        }
        if platform not in platform_map:
            raise ValueError(f"Unknown platform: {platform}")
        return self.daily_budget * platform_map[platform]
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget for the day"""
        return max(0.0, self.daily_budget - self.current_spend)
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment_id": "seg_001",
                "daily_budget": 66.67,
                "platform_split": {
                    "google_ads": 0.40,
                    "meta_ads": 0.40,
                    "programmatic": 0.20
                },
                "max_cpc": 2.50,
                "current_spend": 25.50
            }
        }


class BudgetAllocation(BaseModel):
    """Complete budget allocation plan for a campaign"""
    
    campaign_id: str = Field(..., description="Associated campaign ID")
    total_budget: float = Field(..., ge=100.0, le=100000.0, description="Total monthly budget")
    daily_budget: float = Field(..., gt=0.0, description="Daily budget (total/30)")
    test_budget: float = Field(..., ge=0.0, description="Budget reserved for testing")
    
    allocations: List[SegmentAllocation] = Field(..., min_length=1, description="Segment allocations")
    
    # Tracking
    total_spent: float = Field(default=0.0, ge=0.0, description="Total amount spent")
    remaining_budget: float = Field(..., ge=0.0, description="Remaining budget")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    @model_validator(mode='after')
    def validate_budget_constraints(self) -> 'BudgetAllocation':
        """Validate budget allocation constraints"""
        # Check daily budget calculation
        expected_daily = self.total_budget / 30
        if abs(self.daily_budget - expected_daily) > 0.01:
            raise ValueError(f"Daily budget should be total_budget/30")
        
        # Check test budget is 20% of total
        expected_test = self.total_budget * 0.20
        if abs(self.test_budget - expected_test) > 0.01:
            raise ValueError(f"Test budget should be 20% of total budget")
        
        # Check total allocated doesn't exceed budget (with 5% tolerance)
        total_allocated = sum(alloc.daily_budget for alloc in self.allocations) * 30
        main_budget = self.total_budget - self.test_budget
        if total_allocated > main_budget * 1.05:
            raise ValueError(f"Total allocated ({total_allocated}) exceeds main budget by more than 5%")
        
        # Check remaining budget calculation
        expected_remaining = self.total_budget - self.total_spent
        if abs(self.remaining_budget - expected_remaining) > 0.01:
            raise ValueError(f"Remaining budget calculation is incorrect")
        
        return self
    
    def get_total_daily_allocation(self) -> float:
        """Get total daily budget across all segments"""
        return sum(alloc.daily_budget for alloc in self.allocations)
    
    def get_allocation_by_segment(self, segment_id: str) -> SegmentAllocation:
        """Get allocation for a specific segment"""
        for alloc in self.allocations:
            if alloc.segment_id == segment_id:
                return alloc
        raise ValueError(f"No allocation found for segment: {segment_id}")
    
    def update_spend(self, amount: float) -> None:
        """Update total spend and remaining budget"""
        if amount < 0:
            raise ValueError("Spend amount cannot be negative")
        self.total_spent += amount
        self.remaining_budget = max(0.0, self.total_budget - self.total_spent)
        self.last_updated = datetime.utcnow()
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "total_budget": 5000.0,
                "daily_budget": 166.67,
                "test_budget": 1000.0,
                "allocations": [
                    {
                        "segment_id": "seg_001",
                        "daily_budget": 66.67,
                        "platform_split": {
                            "google_ads": 0.40,
                            "meta_ads": 0.40,
                            "programmatic": 0.20
                        },
                        "max_cpc": 2.50,
                        "current_spend": 25.50
                    }
                ],
                "total_spent": 1250.0,
                "remaining_budget": 3750.0
            }
        }
