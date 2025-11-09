"""End-to-end test suite for Firestore data persistence

Tests data persistence and retrieval from Firestore including:
- Campaign CRUD operations
- Creative variant persistence
- Audience segment persistence
- Budget allocation persistence
- Performance metrics persistence

Requirements: 13.1, 13.4
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
import uuid

# Test imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.campaign import Campaign, CampaignStatus, OptimizationMode
from src.models.creative import CreativeVariant
from src.models.audience import AudienceSegment
from src.models.budget import BudgetAllocation, SegmentAllocation
from src.models.metrics import PerformanceMetrics, VariantMetrics
from src.services.firestore import FirestoreService, get_firestore_service


class TestFirestorePersistence:
    """Test Firestore data persistence and retrieval"""
    
    @pytest.fixture
    def firestore_service(self) -> FirestoreService:
        """Get Firestore service instance"""
        return get_firestore_service()
    
    @pytest.fixture
    def sample_campaign(self) -> Campaign:
        """Create a sample campaign for testing"""
        campaign_id = f"camp_test_{uuid.uuid4().hex[:12]}"
        return Campaign(
            campaign_id=campaign_id,
            account_id="acc_test_123",
            status=CampaignStatus.DRAFT,
            business_goal="increase_sales",
            monthly_budget=5000.0,
            target_audience="small business owners aged 30-50",
            products=["CRM Software", "Project Management Tool"],
            optimization_mode=OptimizationMode.STANDARD
        )
    
    @pytest.fixture
    def sample_creative_variants(self, sample_campaign: Campaign) -> list:
        """Create sample creative variants"""
        return [
            {
                "variant_id": f"var_{uuid.uuid4().hex[:8]}",
                "campaign_id": sample_campaign.campaign_id,
                "status": "active",
                "headlines": {
                    "short": "Save 50% Today",
                    "medium": "Limited Time: Save 50% on Premium Plans",
                    "long": "Don't Miss Out: Save 50% on All Premium Plans This Week Only"
                },
                "body": "Upgrade your business with our premium features. Easy setup, no contracts.",
                "cta": "Get Started Now",
                "compliance_score": 0.95,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0.0,
                "roas": 0.0
            },
            {
                "variant_id": f"var_{uuid.uuid4().hex[:8]}",
                "campaign_id": sample_campaign.campaign_id,
                "status": "active",
                "headlines": {
                    "short": "Try Free",
                    "medium": "Try Free for 30 Days",
                    "long": "Try Our Premium Plan Free for 30 Days - No Credit Card Required"
                },
                "body": "Start your free trial today. Cancel anytime, no questions asked.",
                "cta": "Start Free Trial",
                "compliance_score": 0.92,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0.0,
                "roas": 0.0
            }
        ]
    
    @pytest.fixture
    def sample_audience_segments(self, sample_campaign: Campaign) -> list:
        """Create sample audience segments"""
        return [
            {
                "segment_id": f"seg_{uuid.uuid4().hex[:8]}",
                "campaign_id": sample_campaign.campaign_id,
                "name": "Tech-Savvy Business Owners",
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
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0.0,
                "roas": 0.0
            },
            {
                "segment_id": f"seg_{uuid.uuid4().hex[:8]}",
                "campaign_id": sample_campaign.campaign_id,
                "name": "Traditional Business Owners",
                "demographics": {
                    "age_range": "40-60",
                    "gender": "all",
                    "income": "40k-120k"
                },
                "interests": ["business management", "efficiency"],
                "behaviors": ["traditional marketing", "local business"],
                "estimated_size": "large",
                "conversion_probability": 0.08,
                "priority_score": 0.65,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "spend": 0.0,
                "roas": 0.0
            }
        ]
    
    @pytest.mark.asyncio
    async def test_firestore_service_initialization(self, firestore_service: FirestoreService):
        """Test Firestore service initialization"""
        assert firestore_service is not None
        assert firestore_service.db is not None
        
        print("✓ Firestore service initialized successfully")
    
    @pytest.mark.asyncio
    async def test_campaign_creation(self, firestore_service: FirestoreService, sample_campaign: Campaign):
        """Test campaign creation in Firestore"""
        # Create campaign
        await firestore_service.create_campaign(sample_campaign)
        
        # Verify campaign was created
        retrieved_campaign = await firestore_service.get_campaign(sample_campaign.campaign_id)
        
        assert retrieved_campaign is not None
        assert retrieved_campaign.campaign_id == sample_campaign.campaign_id
        assert retrieved_campaign.account_id == sample_campaign.account_id
        assert retrieved_campaign.status == sample_campaign.status
        assert retrieved_campaign.business_goal == sample_campaign.business_goal
        assert retrieved_campaign.monthly_budget == sample_campaign.monthly_budget
        
        print(f"✓ Campaign created and retrieved successfully")
        print(f"    Campaign ID: {retrieved_campaign.campaign_id}")
        print(f"    Status: {retrieved_campaign.status}")
    
    @pytest.mark.asyncio
    async def test_campaign_update(self, firestore_service: FirestoreService, sample_campaign: Campaign):
        """Test campaign update in Firestore"""
        # Create campaign
        await firestore_service.create_campaign(sample_campaign)
        
        # Update campaign
        update_data = {
            "status": CampaignStatus.ACTIVE.value,
            "monthly_budget": 7500.0,
            "optimization_mode": OptimizationMode.AGGRESSIVE.value
        }
        
        await firestore_service.update_campaign(sample_campaign.campaign_id, update_data)
        
        # Verify updates
        updated_campaign = await firestore_service.get_campaign(sample_campaign.campaign_id)
        
        assert updated_campaign.status == CampaignStatus.ACTIVE
        assert updated_campaign.monthly_budget == 7500.0
        assert updated_campaign.optimization_mode == OptimizationMode.AGGRESSIVE
        
        print(f"✓ Campaign updated successfully")
        print(f"    New status: {updated_campaign.status}")
        print(f"    New budget: ${updated_campaign.monthly_budget}")
    
    @pytest.mark.asyncio
    async def test_campaign_retrieval_by_account(self, firestore_service: FirestoreService):
        """Test retrieving campaigns by account ID"""
        account_id = f"acc_test_{uuid.uuid4().hex[:8]}"
        
        # Create multiple campaigns for the same account
        campaigns = []
        for i in range(3):
            campaign = Campaign(
                campaign_id=f"camp_test_{uuid.uuid4().hex[:12]}",
                account_id=account_id,
                status=CampaignStatus.DRAFT if i == 0 else CampaignStatus.ACTIVE,
                business_goal="increase_sales",
                monthly_budget=5000.0 + (i * 1000),
                target_audience="test audience",
                products=["Product A"],
                optimization_mode=OptimizationMode.STANDARD
            )
            await firestore_service.create_campaign(campaign)
            campaigns.append(campaign)
        
        # Retrieve all campaigns for account
        retrieved_campaigns = await firestore_service.get_campaigns_by_account(account_id)
        
        assert len(retrieved_campaigns) == 3
        assert all(c.account_id == account_id for c in retrieved_campaigns)
        
        # Test filtering by status
        active_campaigns = await firestore_service.get_campaigns_by_account(
            account_id,
            status_filter=CampaignStatus.ACTIVE
        )
        
        assert len(active_campaigns) == 2
        assert all(c.status == CampaignStatus.ACTIVE for c in active_campaigns)
        
        print(f"✓ Campaign retrieval by account working")
        print(f"    Total campaigns: {len(retrieved_campaigns)}")
        print(f"    Active campaigns: {len(active_campaigns)}")
    
    @pytest.mark.asyncio
    async def test_creative_variants_persistence(
        self,
        firestore_service: FirestoreService,
        sample_campaign: Campaign,
        sample_creative_variants: list
    ):
        """Test creative variants batch creation"""
        # Create campaign first
        await firestore_service.create_campaign(sample_campaign)
        
        # Batch create variants
        await firestore_service.batch_create_variants(
            sample_campaign.campaign_id,
            sample_creative_variants
        )
        
        # Update campaign with variants
        await firestore_service.update_campaign(
            sample_campaign.campaign_id,
            {"creative_variants": sample_creative_variants}
        )
        
        # Retrieve campaign and verify variants
        retrieved_campaign = await firestore_service.get_campaign(sample_campaign.campaign_id)
        
        assert len(retrieved_campaign.creative_variants) == len(sample_creative_variants)
        assert all(
            v.get("variant_id") in [sv.get("variant_id") for sv in sample_creative_variants]
            for v in retrieved_campaign.creative_variants
        )
        
        print(f"✓ Creative variants persisted successfully")
        print(f"    Variants count: {len(retrieved_campaign.creative_variants)}")
    
    @pytest.mark.asyncio
    async def test_audience_segments_persistence(
        self,
        firestore_service: FirestoreService,
        sample_campaign: Campaign,
        sample_audience_segments: list
    ):
        """Test audience segments batch creation"""
        # Create campaign first
        await firestore_service.create_campaign(sample_campaign)
        
        # Batch create segments
        await firestore_service.batch_create_segments(
            sample_campaign.campaign_id,
            sample_audience_segments
        )
        
        # Update campaign with segments
        await firestore_service.update_campaign(
            sample_campaign.campaign_id,
            {"audience_segments": sample_audience_segments}
        )
        
        # Retrieve campaign and verify segments
        retrieved_campaign = await firestore_service.get_campaign(sample_campaign.campaign_id)
        
        assert len(retrieved_campaign.audience_segments) == len(sample_audience_segments)
        assert all(
            s.get("segment_id") in [ss.get("segment_id") for ss in sample_audience_segments]
            for s in retrieved_campaign.audience_segments
        )
        
        print(f"✓ Audience segments persisted successfully")
        print(f"    Segments count: {len(retrieved_campaign.audience_segments)}")
    
    @pytest.mark.asyncio
    async def test_budget_allocation_persistence(
        self,
        firestore_service: FirestoreService,
        sample_campaign: Campaign
    ):
        """Test budget allocation persistence"""
        # Create campaign first
        await firestore_service.create_campaign(sample_campaign)
        
        # Create budget allocation
        budget_allocation = {
            "total_budget": 5000.0,
            "daily_budget": 166.67,
            "test_budget": 1000.0,
            "allocations": [
                {
                    "segment_id": "seg_001",
                    "daily_budget": 66.67,
                    "platform_split": {
                        "google_ads": 26.67,
                        "meta_ads": 26.67,
                        "programmatic": 13.33
                    },
                    "max_cpc": 2.50,
                    "current_spend": 0.0
                }
            ],
            "total_spent": 0.0,
            "remaining_budget": 5000.0
        }
        
        # Persist allocation
        await firestore_service.create_allocation(
            sample_campaign.campaign_id,
            budget_allocation
        )
        
        # Update campaign with allocation
        await firestore_service.update_campaign(
            sample_campaign.campaign_id,
            {"budget_allocation": budget_allocation}
        )
        
        # Retrieve and verify
        retrieved_campaign = await firestore_service.get_campaign(sample_campaign.campaign_id)
        
        assert retrieved_campaign.budget_allocation is not None
        assert retrieved_campaign.budget_allocation.get("total_budget") == 5000.0
        assert len(retrieved_campaign.budget_allocation.get("allocations", [])) > 0
        
        print(f"✓ Budget allocation persisted successfully")
        print(f"    Total budget: ${retrieved_campaign.budget_allocation.get('total_budget')}")
    
    @pytest.mark.asyncio
    async def test_performance_metrics_persistence(
        self,
        firestore_service: FirestoreService,
        sample_campaign: Campaign
    ):
        """Test performance metrics persistence"""
        # Create campaign first
        await firestore_service.create_campaign(sample_campaign)
        
        # Create performance metrics
        metrics = PerformanceMetrics(
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
                )
            ],
            by_segment=[],
            by_platform={}
        )
        
        # Calculate aggregate metrics
        metrics.calculate_aggregate_metrics()
        
        # Save metrics
        await firestore_service.save_metrics(metrics)
        
        # Retrieve metrics
        retrieved_metrics = await firestore_service.get_latest_metrics(sample_campaign.campaign_id)
        
        assert retrieved_metrics is not None
        assert retrieved_metrics.campaign_id == sample_campaign.campaign_id
        assert retrieved_metrics.total_spend == 1250.50
        assert retrieved_metrics.total_conversions == 45
        assert retrieved_metrics.roas > 0
        
        print(f"✓ Performance metrics persisted successfully")
        print(f"    ROAS: {retrieved_metrics.roas:.2f}")
        print(f"    Total spend: ${retrieved_metrics.total_spend}")
    
    @pytest.mark.asyncio
    async def test_complete_persistence_workflow(
        self,
        firestore_service: FirestoreService,
        sample_campaign: Campaign,
        sample_creative_variants: list,
        sample_audience_segments: list
    ):
        """Test complete end-to-end data persistence workflow
        
        This is the main integration test that verifies:
        1. Campaign is created
        2. Creative variants are persisted
        3. Audience segments are persisted
        4. Budget allocation is persisted
        5. Performance metrics are persisted
        6. All data can be retrieved correctly
        7. Data relationships are maintained
        """
        print("\n" + "="*60)
        print("COMPLETE FIRESTORE PERSISTENCE WORKFLOW TEST")
        print("="*60)
        
        # Step 1: Create campaign
        print("\n[Step 1] Creating campaign...")
        await firestore_service.create_campaign(sample_campaign)
        print(f"✓ Campaign created: {sample_campaign.campaign_id}")
        
        # Step 2: Persist creative variants
        print("\n[Step 2] Persisting creative variants...")
        await firestore_service.batch_create_variants(
            sample_campaign.campaign_id,
            sample_creative_variants
        )
        await firestore_service.update_campaign(
            sample_campaign.campaign_id,
            {"creative_variants": sample_creative_variants}
        )
        print(f"✓ {len(sample_creative_variants)} creative variants persisted")
        
        # Step 3: Persist audience segments
        print("\n[Step 3] Persisting audience segments...")
        await firestore_service.batch_create_segments(
            sample_campaign.campaign_id,
            sample_audience_segments
        )
        await firestore_service.update_campaign(
            sample_campaign.campaign_id,
            {"audience_segments": sample_audience_segments}
        )
        print(f"✓ {len(sample_audience_segments)} audience segments persisted")
        
        # Step 4: Persist budget allocation
        print("\n[Step 4] Persisting budget allocation...")
        budget_allocation = {
            "total_budget": sample_campaign.monthly_budget,
            "daily_budget": sample_campaign.monthly_budget / 30,
            "test_budget": sample_campaign.monthly_budget * 0.20,
            "allocations": [],
            "total_spent": 0.0,
            "remaining_budget": sample_campaign.monthly_budget
        }
        await firestore_service.create_allocation(
            sample_campaign.campaign_id,
            budget_allocation
        )
        await firestore_service.update_campaign(
            sample_campaign.campaign_id,
            {"budget_allocation": budget_allocation}
        )
        print(f"✓ Budget allocation persisted")
        
        # Step 5: Persist performance metrics
        print("\n[Step 5] Persisting performance metrics...")
        metrics = PerformanceMetrics(
            campaign_id=sample_campaign.campaign_id,
            total_spend=0.0,
            total_impressions=0,
            total_clicks=0,
            total_conversions=0,
            total_revenue=0.0,
            by_variant=[],
            by_segment=[],
            by_platform={}
        )
        await firestore_service.save_metrics(metrics)
        print(f"✓ Performance metrics persisted")
        
        # Step 6: Retrieve complete campaign
        print("\n[Step 6] Retrieving complete campaign...")
        complete_campaign = await firestore_service.get_campaign(sample_campaign.campaign_id)
        
        assert complete_campaign is not None
        assert complete_campaign.campaign_id == sample_campaign.campaign_id
        assert len(complete_campaign.creative_variants) == len(sample_creative_variants)
        assert len(complete_campaign.audience_segments) == len(sample_audience_segments)
        assert complete_campaign.budget_allocation is not None
        print(f"✓ Complete campaign retrieved successfully")
        
        # Step 7: Verify data integrity
        print("\n[Step 7] Verifying data integrity...")
        assert complete_campaign.account_id == sample_campaign.account_id
        assert complete_campaign.business_goal == sample_campaign.business_goal
        assert complete_campaign.monthly_budget == sample_campaign.monthly_budget
        
        # Verify variant IDs match
        variant_ids = [v.get("variant_id") for v in complete_campaign.creative_variants]
        expected_variant_ids = [v.get("variant_id") for v in sample_creative_variants]
        assert all(vid in expected_variant_ids for vid in variant_ids)
        
        # Verify segment IDs match
        segment_ids = [s.get("segment_id") for s in complete_campaign.audience_segments]
        expected_segment_ids = [s.get("segment_id") for s in sample_audience_segments]
        assert all(sid in expected_segment_ids for sid in segment_ids)
        
        print(f"✓ Data integrity verified")
        
        print("\n" + "="*60)
        print("FIRESTORE PERSISTENCE WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"\nPersistence Summary:")
        print(f"  - Campaign ID: {complete_campaign.campaign_id}")
        print(f"  - Account ID: {complete_campaign.account_id}")
        print(f"  - Creative Variants: {len(complete_campaign.creative_variants)}")
        print(f"  - Audience Segments: {len(complete_campaign.audience_segments)}")
        print(f"  - Budget Allocated: ${complete_campaign.budget_allocation.get('total_budget', 0):.2f}")
        print(f"  - Status: {complete_campaign.status}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("END-TO-END FIRESTORE PERSISTENCE TEST SUITE")
    print("="*60 + "\n")
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])
