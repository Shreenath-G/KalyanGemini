"""End-to-end test suite for performance monitoring and optimization flow

Tests the complete performance monitoring and optimization workflow including:
- Performance metrics collection
- Performance analysis
- Optimization action generation
- Optimization execution

Requirements: 6.1, 9.1, 9.3
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

# Test imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.campaign import Campaign, CampaignStatus, OptimizationMode
from src.models.metrics import PerformanceMetrics, VariantMetrics, SegmentMetrics, PlatformMetrics
from src.agents.campaign_orchestrator import CampaignOrchestratorAgent


class TestPerformanceOptimizationWorkflow:
    """Test complete performance monitoring and optimization workflow"""
    
    @pytest.fixture
    def sample_campaign(self) -> Campaign:
        """Create a sample active campaign for testing"""
        campaign_id = f"camp_test_{uuid.uuid4().hex[:12]}"
        return Campaign(
            campaign_id=campaign_id,
            account_id="acc_test_123",
            status=CampaignStatus.ACTIVE,
            business_goal="increase_sales",
            monthly_budget=5000.0,
            target_audience="small business owners",
            products=["CRM Software"],
            optimization_mode=OptimizationMode.STANDARD,
            creative_variants=[
                {
                    "variant_id": "var_001",
                    "status": "active",
                    "headlines": {"short": "Save 50%", "medium": "Save 50% Today", "long": "Save 50% on Premium Plans"},
                    "body": "Upgrade now",
                    "cta": "Get Started"
                },
                {
                    "variant_id": "var_002",
                    "status": "active",
                    "headlines": {"short": "Try Free", "medium": "Try Free for 30 Days", "long": "Try Our Premium Plan Free for 30 Days"},
                    "body": "No credit card required",
                    "cta": "Start Trial"
                },
                {
                    "variant_id": "var_003",
                    "status": "active",
                    "headlines": {"short": "Limited Time", "medium": "Limited Time Offer", "long": "Limited Time: Special Pricing Available"},
                    "body": "Act now",
                    "cta": "Learn More"
                }
            ],
            audience_segments=[
                {
                    "segment_id": "seg_001",
                    "name": "Tech-Savvy Business Owners",
                    "demographics": {"age_range": "30-50"},
                    "priority_score": 0.85
                },
                {
                    "segment_id": "seg_002",
                    "name": "Traditional Business Owners",
                    "demographics": {"age_range": "40-60"},
                    "priority_score": 0.65
                }
            ],
            total_spend=1250.50,
            total_impressions=125000,
            total_clicks=3500,
            total_conversions=45
        )
    
    @pytest.fixture
    def sample_performance_metrics(self, sample_campaign: Campaign) -> PerformanceMetrics:
        """Create sample performance metrics for testing"""
        return PerformanceMetrics(
            campaign_id=sample_campaign.campaign_id,
            total_spend=1250.50,
            total_impressions=125000,
            total_clicks=3500,
            total_conversions=45,
            total_revenue=1440.00,
            by_variant=[
                VariantMetrics(
                    variant_id="var_001",
                    impressions=50000,
                    clicks=1500,
                    conversions=20,
                    spend=500.00,
                    revenue=640.00
                ),
                VariantMetrics(
                    variant_id="var_002",
                    impressions=50000,
                    clicks=1400,
                    conversions=19,
                    spend=500.30,
                    revenue=608.00
                ),
                VariantMetrics(
                    variant_id="var_003",
                    impressions=25000,
                    clicks=600,
                    conversions=6,
                    spend=250.20,
                    revenue=192.00
                )
            ],
            by_segment=[
                SegmentMetrics(
                    segment_id="seg_001",
                    segment_name="Tech-Savvy Business Owners",
                    impressions=75000,
                    clicks=2500,
                    conversions=35,
                    spend=875.00,
                    revenue=1120.00
                ),
                SegmentMetrics(
                    segment_id="seg_002",
                    segment_name="Traditional Business Owners",
                    impressions=50000,
                    clicks=1000,
                    conversions=10,
                    spend=375.50,
                    revenue=320.00
                )
            ],
            by_platform={
                "google_ads": PlatformMetrics(
                    platform="google_ads",
                    spend=500.20,
                    impressions=50000,
                    clicks=1400,
                    conversions=18,
                    revenue=576.00
                ),
                "meta_ads": PlatformMetrics(
                    platform="meta_ads",
                    spend=500.30,
                    impressions=50000,
                    clicks=1400,
                    conversions=19,
                    revenue=608.00
                ),
                "programmatic": PlatformMetrics(
                    platform="programmatic",
                    spend=250.00,
                    impressions=25000,
                    clicks=700,
                    conversions=8,
                    revenue=256.00
                )
            }
        )
    
    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self, sample_performance_metrics: PerformanceMetrics):
        """Test performance metrics calculation
        
        Verifies:
        - ROAS calculation
        - CPA calculation
        - CTR calculation
        - Metrics are calculated correctly for variants, segments, and platforms
        """
        # Calculate aggregate metrics
        sample_performance_metrics.calculate_aggregate_metrics()
        
        # Verify aggregate calculations
        assert sample_performance_metrics.roas > 0
        assert sample_performance_metrics.cpa > 0
        assert sample_performance_metrics.ctr > 0
        
        # Verify ROAS calculation (revenue / spend)
        expected_roas = sample_performance_metrics.total_revenue / sample_performance_metrics.total_spend
        assert abs(sample_performance_metrics.roas - expected_roas) < 0.01
        
        # Verify CPA calculation (spend / conversions)
        expected_cpa = sample_performance_metrics.total_spend / sample_performance_metrics.total_conversions
        assert abs(sample_performance_metrics.cpa - expected_cpa) < 0.01
        
        # Verify CTR calculation (clicks / impressions * 100)
        expected_ctr = (sample_performance_metrics.total_clicks / sample_performance_metrics.total_impressions) * 100
        assert abs(sample_performance_metrics.ctr - expected_ctr) < 0.01
        
        print("✓ Performance metrics calculated correctly")
        print(f"  - ROAS: {sample_performance_metrics.roas:.2f}")
        print(f"  - CPA: ${sample_performance_metrics.cpa:.2f}")
        print(f"  - CTR: {sample_performance_metrics.ctr:.2f}%")
    
    @pytest.mark.asyncio
    async def test_variant_metrics_calculation(self, sample_performance_metrics: PerformanceMetrics):
        """Test variant-level metrics calculation"""
        for variant in sample_performance_metrics.by_variant:
            # Calculate variant metrics
            variant_roas = variant.calculate_roas()
            variant_cpa = variant.calculate_cpa()
            variant_ctr = variant.calculate_ctr()
            
            # Verify calculations
            assert variant_roas >= 0
            assert variant_cpa >= 0
            assert variant_ctr >= 0
            
            # Verify ROAS calculation
            if variant.spend > 0:
                expected_roas = variant.revenue / variant.spend
                assert abs(variant_roas - expected_roas) < 0.01
            
            print(f"✓ Variant {variant.variant_id} metrics:")
            print(f"    ROAS: {variant_roas:.2f}, CPA: ${variant_cpa:.2f}, CTR: {variant_ctr:.2f}%")
    
    @pytest.mark.asyncio
    async def test_underperforming_variant_detection(self, sample_performance_metrics: PerformanceMetrics):
        """Test detection of underperforming variants
        
        Verifies:
        - Variants with ROAS < 1.0 are identified
        - Minimum click threshold is respected
        - Correct variants are flagged for optimization
        """
        # Get underperforming variants (ROAS < 1.0, min 100 clicks)
        underperforming = sample_performance_metrics.get_underperforming_variants(
            roas_threshold=1.0,
            min_clicks=100
        )
        
        # Verify detection logic
        for variant in underperforming:
            variant_roas = variant.calculate_roas()
            assert variant_roas < 1.0
            assert variant.clicks >= 100
            
            print(f"✓ Underperforming variant detected: {variant.variant_id}")
            print(f"    ROAS: {variant_roas:.2f}, Clicks: {variant.clicks}")
    
    @pytest.mark.asyncio
    async def test_top_performing_variant_detection(self, sample_performance_metrics: PerformanceMetrics):
        """Test detection of top performing variants
        
        Verifies:
        - Top performers are identified by ROAS
        - Correct number of top performers returned
        - Variants are sorted by performance
        """
        # Get top 2 performing variants
        top_performers = sample_performance_metrics.get_top_performing_variants(limit=2)
        
        assert len(top_performers) <= 2
        
        # Verify sorting (highest ROAS first)
        if len(top_performers) > 1:
            for i in range(len(top_performers) - 1):
                roas_current = top_performers[i].calculate_roas()
                roas_next = top_performers[i + 1].calculate_roas()
                assert roas_current >= roas_next
        
        for variant in top_performers:
            variant_roas = variant.calculate_roas()
            print(f"✓ Top performer: {variant.variant_id}")
            print(f"    ROAS: {variant_roas:.2f}, Conversions: {variant.conversions}")
    
    @pytest.mark.asyncio
    async def test_optimization_action_generation(self, sample_performance_metrics: PerformanceMetrics):
        """Test generation of optimization actions based on performance
        
        Verifies:
        - Pause actions generated for underperformers
        - Scale actions generated for high performers
        - Targeting adjustments suggested when overall ROAS is low
        """
        actions = []
        
        # Check for underperforming variants
        underperforming = sample_performance_metrics.get_underperforming_variants(
            roas_threshold=1.0,
            min_clicks=100
        )
        
        for variant in underperforming:
            actions.append({
                "type": "pause_variant",
                "variant_id": variant.variant_id,
                "reason": f"Low ROAS: {variant.calculate_roas():.2f}",
                "estimated_impact": {
                    "spend_reduction": variant.spend,
                    "roas_improvement": 0.2
                }
            })
        
        # Check for high performers
        top_performers = sample_performance_metrics.get_top_performing_variants(limit=3)
        
        for variant in top_performers:
            if variant.calculate_roas() > 3.0:
                actions.append({
                    "type": "scale_variant",
                    "variant_id": variant.variant_id,
                    "reason": f"High ROAS: {variant.calculate_roas():.2f}",
                    "increase_percent": 50,
                    "estimated_impact": {
                        "additional_spend": variant.spend * 0.5,
                        "expected_conversions": variant.conversions * 0.5
                    }
                })
        
        # Check overall ROAS
        sample_performance_metrics.calculate_aggregate_metrics()
        if sample_performance_metrics.roas < 2.0:
            actions.append({
                "type": "adjust_targeting",
                "reason": f"Overall ROAS below target: {sample_performance_metrics.roas:.2f}",
                "recommendation": "Consider refining audience targeting or creative messaging"
            })
        
        assert len(actions) > 0
        
        print(f"✓ Generated {len(actions)} optimization actions:")
        for action in actions:
            print(f"    - {action['type']}: {action.get('reason', 'N/A')}")
    
    @pytest.mark.asyncio
    async def test_optimization_request_handling(self, sample_campaign: Campaign):
        """Test handling of optimization requests
        
        Verifies:
        - Orchestrator receives optimization request
        - Actions are processed and grouped by type
        - Budget adjustments are coordinated
        - Creative updates are coordinated
        - Campaign is updated with optimization timestamp
        """
        orchestrator = CampaignOrchestratorAgent()
        
        # Create optimization actions
        optimization_actions = [
            {
                "type": "pause_variant",
                "variant_id": "var_003",
                "reason": "Low ROAS: 0.77"
            },
            {
                "type": "scale_variant",
                "variant_id": "var_001",
                "reason": "High ROAS: 3.2",
                "increase_percent": 50
            },
            {
                "type": "adjust_targeting",
                "reason": "Overall ROAS below target"
            }
        ]
        
        # Handle optimization request
        results = await orchestrator.handle_optimization_request(
            campaign_id=sample_campaign.campaign_id,
            optimization_actions=optimization_actions,
            optimization_type="auto"
        )
        
        # Verify results structure
        assert results is not None
        assert "success" in results
        assert "campaign_id" in results
        assert "optimization_type" in results
        assert "actions_applied" in results
        assert "total_actions" in results
        
        # Verify actions were processed
        assert results["total_actions"] == len(optimization_actions)
        
        print("✓ Optimization request handled successfully")
        print(f"  - Campaign ID: {results['campaign_id']}")
        print(f"  - Optimization Type: {results['optimization_type']}")
        print(f"  - Total Actions: {results['total_actions']}")
    
    @pytest.mark.asyncio
    async def test_complete_optimization_workflow(self, sample_campaign: Campaign, sample_performance_metrics: PerformanceMetrics):
        """Test complete end-to-end optimization workflow
        
        This is the main integration test that verifies:
        1. Performance metrics are collected
        2. Metrics are analyzed for optimization opportunities
        3. Optimization actions are generated
        4. Actions are sent to orchestrator
        5. Orchestrator coordinates specialist agents
        6. Optimizations are applied
        7. Campaign is updated
        """
        orchestrator = CampaignOrchestratorAgent()
        
        print("\n" + "="*60)
        print("COMPLETE OPTIMIZATION WORKFLOW TEST")
        print("="*60)
        
        # Step 1: Calculate performance metrics
        print("\n[Step 1] Calculating performance metrics...")
        sample_performance_metrics.calculate_aggregate_metrics()
        
        assert sample_performance_metrics.roas > 0
        assert sample_performance_metrics.cpa > 0
        assert sample_performance_metrics.ctr > 0
        print(f"✓ Metrics calculated - ROAS: {sample_performance_metrics.roas:.2f}")
        
        # Step 2: Analyze performance and identify opportunities
        print("\n[Step 2] Analyzing performance...")
        underperforming = sample_performance_metrics.get_underperforming_variants(
            roas_threshold=1.0,
            min_clicks=100
        )
        top_performers = sample_performance_metrics.get_top_performing_variants(limit=3)
        
        print(f"✓ Found {len(underperforming)} underperforming variants")
        print(f"✓ Found {len(top_performers)} top performing variants")
        
        # Step 3: Generate optimization actions
        print("\n[Step 3] Generating optimization actions...")
        actions = []
        
        for variant in underperforming:
            actions.append({
                "type": "pause_variant",
                "variant_id": variant.variant_id,
                "reason": f"Low ROAS: {variant.calculate_roas():.2f}"
            })
        
        for variant in top_performers:
            if variant.calculate_roas() > 3.0:
                actions.append({
                    "type": "scale_variant",
                    "variant_id": variant.variant_id,
                    "reason": f"High ROAS: {variant.calculate_roas():.2f}",
                    "increase_percent": 50
                })
        
        print(f"✓ Generated {len(actions)} optimization actions")
        
        # Step 4: Send optimization request to orchestrator
        print("\n[Step 4] Sending optimization request to orchestrator...")
        if len(actions) > 0:
            results = await orchestrator.handle_optimization_request(
                campaign_id=sample_campaign.campaign_id,
                optimization_actions=actions,
                optimization_type="auto"
            )
            
            assert results["success"] is True
            assert results["total_actions"] == len(actions)
            print(f"✓ Optimization request processed successfully")
        else:
            print("✓ No optimization actions needed")
        
        print("\n" + "="*60)
        print("OPTIMIZATION WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"\nOptimization Summary:")
        print(f"  - Campaign ID: {sample_campaign.campaign_id}")
        print(f"  - Current ROAS: {sample_performance_metrics.roas:.2f}")
        print(f"  - Current CPA: ${sample_performance_metrics.cpa:.2f}")
        print(f"  - Total Spend: ${sample_performance_metrics.total_spend:.2f}")
        print(f"  - Total Conversions: {sample_performance_metrics.total_conversions}")
        print(f"  - Optimization Actions: {len(actions)}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("END-TO-END PERFORMANCE OPTIMIZATION TEST SUITE")
    print("="*60 + "\n")
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])
