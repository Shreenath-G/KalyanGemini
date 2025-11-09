"""Performance metrics data models"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from datetime import datetime


class VariantMetrics(BaseModel):
    """Performance metrics for a creative variant"""
    
    variant_id: str = Field(..., description="Creative variant identifier")
    impressions: int = Field(default=0, ge=0, description="Total impressions")
    clicks: int = Field(default=0, ge=0, description="Total clicks")
    conversions: int = Field(default=0, ge=0, description="Total conversions")
    spend: float = Field(default=0.0, ge=0.0, description="Total spend")
    revenue: float = Field(default=0.0, ge=0.0, description="Total revenue generated")
    
    def calculate_roas(self) -> float:
        """Calculate Return on Ad Spend"""
        if self.spend == 0:
            return 0.0
        return self.revenue / self.spend
    
    def calculate_cpa(self) -> float:
        """Calculate Cost Per Acquisition"""
        if self.conversions == 0:
            return 0.0
        return self.spend / self.conversions
    
    def calculate_ctr(self) -> float:
        """Calculate Click-Through Rate (percentage)"""
        if self.impressions == 0:
            return 0.0
        return (self.clicks / self.impressions) * 100
    
    def calculate_conversion_rate(self) -> float:
        """Calculate conversion rate (percentage)"""
        if self.clicks == 0:
            return 0.0
        return (self.conversions / self.clicks) * 100
    
    class Config:
        json_schema_extra = {
            "example": {
                "variant_id": "var_001",
                "impressions": 10000,
                "clicks": 500,
                "conversions": 25,
                "spend": 250.0,
                "revenue": 800.0
            }
        }


class SegmentMetrics(BaseModel):
    """Performance metrics for an audience segment"""
    
    segment_id: str = Field(..., description="Audience segment identifier")
    impressions: int = Field(default=0, ge=0, description="Total impressions")
    clicks: int = Field(default=0, ge=0, description="Total clicks")
    conversions: int = Field(default=0, ge=0, description="Total conversions")
    spend: float = Field(default=0.0, ge=0.0, description="Total spend")
    revenue: float = Field(default=0.0, ge=0.0, description="Total revenue generated")
    
    def calculate_roas(self) -> float:
        """Calculate Return on Ad Spend"""
        if self.spend == 0:
            return 0.0
        return self.revenue / self.spend
    
    def calculate_cpa(self) -> float:
        """Calculate Cost Per Acquisition"""
        if self.conversions == 0:
            return 0.0
        return self.spend / self.conversions
    
    def calculate_ctr(self) -> float:
        """Calculate Click-Through Rate (percentage)"""
        if self.impressions == 0:
            return 0.0
        return (self.clicks / self.impressions) * 100
    
    def calculate_conversion_rate(self) -> float:
        """Calculate conversion rate (percentage)"""
        if self.clicks == 0:
            return 0.0
        return (self.conversions / self.clicks) * 100
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment_id": "seg_001",
                "impressions": 25000,
                "clicks": 1250,
                "conversions": 62,
                "spend": 625.0,
                "revenue": 2187.5
            }
        }


class PlatformMetrics(BaseModel):
    """Performance metrics for an advertising platform"""
    
    platform_name: str = Field(..., description="Platform name (google_ads, meta_ads, programmatic)")
    impressions: int = Field(default=0, ge=0, description="Total impressions")
    clicks: int = Field(default=0, ge=0, description="Total clicks")
    conversions: int = Field(default=0, ge=0, description="Total conversions")
    spend: float = Field(default=0.0, ge=0.0, description="Total spend")
    revenue: float = Field(default=0.0, ge=0.0, description="Total revenue generated")
    
    @field_validator('platform_name')
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate platform name"""
        valid_platforms = ['google_ads', 'meta_ads', 'programmatic']
        if v not in valid_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return v
    
    def calculate_roas(self) -> float:
        """Calculate Return on Ad Spend"""
        if self.spend == 0:
            return 0.0
        return self.revenue / self.spend
    
    def calculate_cpa(self) -> float:
        """Calculate Cost Per Acquisition"""
        if self.conversions == 0:
            return 0.0
        return self.spend / self.conversions
    
    def calculate_ctr(self) -> float:
        """Calculate Click-Through Rate (percentage)"""
        if self.impressions == 0:
            return 0.0
        return (self.clicks / self.impressions) * 100
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform_name": "google_ads",
                "impressions": 20000,
                "clicks": 1000,
                "conversions": 50,
                "spend": 500.0,
                "revenue": 1750.0
            }
        }


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics for a campaign"""
    
    campaign_id: str = Field(..., description="Campaign identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    
    # Aggregate metrics
    total_spend: float = Field(default=0.0, ge=0.0, description="Total spend")
    total_impressions: int = Field(default=0, ge=0, description="Total impressions")
    total_clicks: int = Field(default=0, ge=0, description="Total clicks")
    total_conversions: int = Field(default=0, ge=0, description="Total conversions")
    total_revenue: float = Field(default=0.0, ge=0.0, description="Total revenue generated")
    
    # Calculated metrics (computed from aggregates)
    roas: float = Field(default=0.0, ge=0.0, description="Return on Ad Spend")
    cpa: float = Field(default=0.0, ge=0.0, description="Cost Per Acquisition")
    ctr: float = Field(default=0.0, ge=0.0, description="Click-Through Rate (percentage)")
    conversion_rate: float = Field(default=0.0, ge=0.0, description="Conversion rate (percentage)")
    
    # Breakdowns
    by_variant: List[VariantMetrics] = Field(default_factory=list, description="Metrics by creative variant")
    by_segment: List[SegmentMetrics] = Field(default_factory=list, description="Metrics by audience segment")
    by_platform: Dict[str, PlatformMetrics] = Field(default_factory=dict, description="Metrics by platform")
    
    def calculate_aggregate_metrics(self) -> None:
        """Calculate aggregate metrics from totals"""
        # Calculate ROAS
        if self.total_spend > 0:
            self.roas = self.total_revenue / self.total_spend
        else:
            self.roas = 0.0
        
        # Calculate CPA
        if self.total_conversions > 0:
            self.cpa = self.total_spend / self.total_conversions
        else:
            self.cpa = 0.0
        
        # Calculate CTR
        if self.total_impressions > 0:
            self.ctr = (self.total_clicks / self.total_impressions) * 100
        else:
            self.ctr = 0.0
        
        # Calculate conversion rate
        if self.total_clicks > 0:
            self.conversion_rate = (self.total_conversions / self.total_clicks) * 100
        else:
            self.conversion_rate = 0.0
    
    def get_variant_metrics(self, variant_id: str) -> Optional[VariantMetrics]:
        """Get metrics for a specific variant"""
        for metrics in self.by_variant:
            if metrics.variant_id == variant_id:
                return metrics
        return None
    
    def get_segment_metrics(self, segment_id: str) -> Optional[SegmentMetrics]:
        """Get metrics for a specific segment"""
        for metrics in self.by_segment:
            if metrics.segment_id == segment_id:
                return metrics
        return None
    
    def get_platform_metrics(self, platform_name: str) -> Optional[PlatformMetrics]:
        """Get metrics for a specific platform"""
        return self.by_platform.get(platform_name)
    
    def get_top_performing_variants(self, limit: int = 3) -> List[VariantMetrics]:
        """Get top performing variants by ROAS"""
        sorted_variants = sorted(
            self.by_variant,
            key=lambda v: v.calculate_roas(),
            reverse=True
        )
        return sorted_variants[:limit]
    
    def get_underperforming_variants(self, roas_threshold: float = 1.0, min_clicks: int = 100) -> List[VariantMetrics]:
        """Get underperforming variants below ROAS threshold with minimum clicks"""
        return [
            v for v in self.by_variant
            if v.clicks >= min_clicks and v.calculate_roas() < roas_threshold
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "timestamp": "2024-01-15T10:30:00Z",
                "total_spend": 1250.0,
                "total_impressions": 50000,
                "total_clicks": 2500,
                "total_conversions": 125,
                "total_revenue": 4000.0,
                "roas": 3.2,
                "cpa": 10.0,
                "ctr": 5.0,
                "conversion_rate": 5.0,
                "by_variant": [
                    {
                        "variant_id": "var_001",
                        "impressions": 10000,
                        "clicks": 500,
                        "conversions": 25,
                        "spend": 250.0,
                        "revenue": 800.0
                    }
                ],
                "by_segment": [
                    {
                        "segment_id": "seg_001",
                        "impressions": 25000,
                        "clicks": 1250,
                        "conversions": 62,
                        "spend": 625.0,
                        "revenue": 2187.5
                    }
                ],
                "by_platform": {
                    "google_ads": {
                        "platform_name": "google_ads",
                        "impressions": 20000,
                        "clicks": 1000,
                        "conversions": 50,
                        "spend": 500.0,
                        "revenue": 1750.0
                    }
                }
            }
        }


class MetricsSnapshot(BaseModel):
    """Point-in-time snapshot of campaign metrics for time-series analysis"""
    
    campaign_id: str = Field(..., description="Campaign identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Snapshot timestamp")
    
    # Snapshot values
    spend: float = Field(..., ge=0.0, description="Spend at this point")
    impressions: int = Field(..., ge=0, description="Impressions at this point")
    clicks: int = Field(..., ge=0, description="Clicks at this point")
    conversions: int = Field(..., ge=0, description="Conversions at this point")
    revenue: float = Field(..., ge=0.0, description="Revenue at this point")
    roas: float = Field(..., ge=0.0, description="ROAS at this point")
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "timestamp": "2024-01-15T10:30:00Z",
                "spend": 1250.0,
                "impressions": 50000,
                "clicks": 2500,
                "conversions": 125,
                "revenue": 4000.0,
                "roas": 3.2
            }
        }
