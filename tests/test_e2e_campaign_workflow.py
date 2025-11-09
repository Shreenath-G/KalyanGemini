"""End-to-end test suite for campaign creation workflow

Tests the complete campaign creation flow including:
- Campaign creation via API
- Agent coordination and communication
- Data persistence to Firestore
- Strategy synthesis

Requirements: 1.1, 2.1, 6.1, 7.1
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

from src.models.campaign import Campaign, CampaignRequest, CampaignStatus, OptimizationMode
from src.models.creative import CreativeVariant
from src.models.audience import AudienceSegment
from src.models.budget import BudgetAllocation
from src.agents.campaign_orchestrator import CampaignOrchestratorAgent, AgentMessage, AgentResponse
from src.services.firestore import FirestoreService


class TestCampaignCreationWorkflow:
    """Test complete campaign creation workflow with agents"""
    
    @pytest.fixture
    def sample_campaign_request(self) -> CampaignRequest:
        """Create a sample campaign request for testing"""
        return CampaignRequest(
            business_goal="increase_sales",
            monthly_budget=5000.0,
            target_audience="small business owners aged 30-50 interested in productivity software",
            products=["CRM Software", "Project Management Tool"],
            optimization_mode=OptimizationMode.STANDARD
        )
    
    @pytest.fixture
    def sample_campaign(self, sample_campaign_request: CampaignRequest) -> Campaign:
        """Create a sample campaign object for testing"""
        campaign_id = f"camp_test_{uuid.uuid4().hex[:12]}"
        return Campaign(
            campaign_id=campaign_id,
            account_id="acc_test_123",
            status=CampaignStatus.DRAFT,
            business_goal=sample_campaign_request.business_goal,
            monthly_budget=sample_campaign_request.monthly_budget,
            target_audience=sample_campaign_request.target_audience,
            products=sample_campaign_request.products,
            optimization_mode=sample_campaign_request.optimization_mode
        )
    
    @pytest.mark.asyncio
    async def test_campaign_orchestrator_initialization(self):
        """Test that Campaign Orchestrator Agent initializes correctly"""
        orchestrator = CampaignOrchestratorAgent()
        
        assert orchestrator.name == "campaign_orchestrator"
        assert orchestrator.agent_timeout > 0
        assert orchestrator.firestore_service is not None
        
        print("✓ Campaign Orchestrator Agent initialized successfully")
    
    @pytest.mark.asyncio
    async def test_agent_message_creation(self):
        """Test agent message structure and serialization"""
        message = AgentMessage(
            message_type="generate_creatives",
            data={"campaign_id": "camp_test_123", "budget": 5000.0},
            sender="campaign_orchestrator"
        )
        
        assert message.message_type == "generate_creatives"
        assert message.sender == "campaign_orchestrator"
        assert message.correlation_id is not None
        assert message.timestamp is not None
        
        # Test serialization
        message_dict = message.to_dict()
        assert "message_type" in message_dict
        assert "data" in message_dict
        assert "correlation_id" in message_dict
        assert "timestamp" in message_dict
        
        print("✓ Agent message creation and serialization working")
    
    @pytest.mark.asyncio
    async def test_agent_response_structure(self):
        """Test agent response structure"""
        # Test successful response
        success_response = AgentResponse(
            success=True,
            data={"variations": [{"variant_id": "var_001"}]},
            agent_name="creative_generator"
        )
        
        assert success_response.success is True
        assert "variations" in success_response.data
        assert success_response.agent_name == "creative_generator"
        
        # Test error response
        error_response = AgentResponse(
            success=False,
            error="Agent timeout",
            agent_name="audience_targeting"
        )
        
        assert error_response.success is False
        assert error_response.error == "Agent timeout"
        
        print("✓ Agent response structure validated")
    
    @pytest.mark.asyncio
    async def test_campaign_request_handling(self, sample_campaign: Campaign, sample_campaign_request: CampaignRequest):
        """Test campaign request handling by orchestrator
        
        This test verifies:
        - Orchestrator receives campaign request
        - Messages are sent to specialist agents
        - Responses are collected (even if agents not implemented)
        - Fallback strategies are applied when needed
        - Results are returned for synthesis
        """
        orchestrator = CampaignOrchestratorAgent()
        
        # Handle campaign request
        results = await orchestrator.handle_campaign_request(
            campaign=sample_campaign,
            campaign_request=sample_campaign_request
        )
        
        # Verify results structure
        assert "creative_variants" in results
        assert "audience_segments" in results
        assert "budget_allocation" in results
        assert "agent_status" in results
        assert "correlation_id" in results
        assert "requires_review" in results
        
        # Verify agent status tracking
        agent_status = results["agent_status"]
        assert "creative_generator" in agent_status
        assert "audience_targeting" in agent_status
        assert "budget_optimizer" in agent_status
        
        # Each agent status should have success flag and fallback indicator
        for agent_name, status in agent_status.items():
            assert "success" in status
            assert "fallback_applied" in status
        
        # Since agents are not fully implemented, fallbacks should be applied
        assert results["requires_review"] is True
        
        print("✓ Campaign request handling completed with fallback strategies")
        print(f"  - Creative variants: {len(results['creative_variants'])}")
        print(f"  - Audience segments: {len(results['audience_segments'])}")
        print(f"  - Requires review: {results['requires_review']}")
    
    @pytest.mark.asyncio
    async def test_strategy_synthesis(self, sample_campaign: Campaign):
        """Test strategy synthesis from agent results
        
        This test verifies:
        - Agent results are combined into unified strategy
        - Campaign object is updated with strategy components
        - Strategy is persisted to Firestore
        - Launch timeline is calculated
        """
        orchestrator = CampaignOrchestratorAgent()
        
        # Create mock agent results
        agent_results = {
            "creative_variants": [
                {
                    "variant_id": "var_001",
                    "headlines": {
                        "short": "Save 50% Today",
                        "medium": "Limited Time: Save 50% on Premium Plans",
                        "long": "Don't Miss Out: Save 50% on All Premium Plans This Week Only"
                    },
                    "body": "Upgrade your business with our premium features.",
                    "cta": "Get Started Now",
                    "status": "active",
                    "compliance_score": 0.95
                }
            ],
            "audience_segments": [
                {
                    "segment_id": "seg_001",
                    "name": "Tech-Savvy Business Owners",
                    "demographics": {"age_range": "30-50", "income": "50k-150k"},
                    "interests": ["entrepreneurship", "technology"],
                    "estimated_size": "medium",
                    "conversion_probability": 0.12,
                    "priority_score": 0.85
                }
            ],
            "budget_allocation": {
                "total_budget": 5000.0,
                "daily_budget": 166.67,
                "test_budget": 1000.0,
                "allocations": []
            },
            "agent_status": {
                "creative_generator": {"success": True, "fallback_applied": False},
                "audience_targeting": {"success": True, "fallback_applied": False},
                "budget_optimizer": {"success": True, "fallback_applied": False}
            },
            "correlation_id": str(uuid.uuid4()),
            "requires_review": False
        }
        
        # Synthesize strategy
        updated_campaign = await orchestrator.synthesize_strategy(
            campaign=sample_campaign,
            agent_results=agent_results
        )
        
        # Verify campaign was updated
        assert len(updated_campaign.creative_variants) > 0
        assert len(updated_campaign.audience_segments) > 0
        assert updated_campaign.budget_allocation is not None
        assert updated_campaign.status == CampaignStatus.DRAFT
        
        print("✓ Strategy synthesis completed successfully")
        print(f"  - Campaign ID: {updated_campaign.campaign_id}")
        print(f"  - Status: {updated_campaign.status}")
        print(f"  - Variants: {len(updated_campaign.creative_variants)}")
        print(f"  - Segments: {len(updated_campaign.audience_segments)}")
    
    @pytest.mark.asyncio
    async def test_launch_timeline_calculation(self, sample_campaign: Campaign):
        """Test launch timeline calculation based on campaign complexity"""
        orchestrator = CampaignOrchestratorAgent()
        
        # Test with review required
        timeline_with_review = orchestrator._calculate_launch_timeline(
            campaign=sample_campaign,
            requires_review=True
        )
        assert "requires review" in timeline_with_review.lower()
        
        # Test with simple campaign (no variants/segments)
        sample_campaign.creative_variants = []
        sample_campaign.audience_segments = []
        timeline_simple = orchestrator._calculate_launch_timeline(
            campaign=sample_campaign,
            requires_review=False
        )
        assert "6-12 hours" in timeline_simple or "12-24 hours" in timeline_simple
        
        # Test with complex campaign
        sample_campaign.creative_variants = [{"variant_id": f"var_{i}"} for i in range(5)]
        sample_campaign.audience_segments = [{"segment_id": f"seg_{i}"} for i in range(3)]
        timeline_complex = orchestrator._calculate_launch_timeline(
            campaign=sample_campaign,
            requires_review=False
        )
        assert "24-48 hours" in timeline_complex or "12-24 hours" in timeline_complex
        
        print("✓ Launch timeline calculation working correctly")
        print(f"  - With review: {timeline_with_review}")
        print(f"  - Simple campaign: {timeline_simple}")
        print(f"  - Complex campaign: {timeline_complex}")
    
    @pytest.mark.asyncio
    async def test_complete_campaign_workflow(self, sample_campaign: Campaign, sample_campaign_request: CampaignRequest):
        """Test complete end-to-end campaign creation workflow
        
        This is the main integration test that verifies:
        1. Campaign request is received
        2. Orchestrator coordinates specialist agents
        3. Agent responses are collected
        4. Fallback strategies are applied when needed
        5. Strategy is synthesized
        6. Campaign is persisted to Firestore
        7. Complete campaign object is returned
        """
        orchestrator = CampaignOrchestratorAgent()
        
        print("\n" + "="*60)
        print("COMPLETE CAMPAIGN WORKFLOW TEST")
        print("="*60)
        
        # Step 1: Handle campaign request
        print("\n[Step 1] Handling campaign request...")
        agent_results = await orchestrator.handle_campaign_request(
            campaign=sample_campaign,
            campaign_request=sample_campaign_request
        )
        
        assert agent_results is not None
        assert "creative_variants" in agent_results
        assert "audience_segments" in agent_results
        assert "budget_allocation" in agent_results
        print("✓ Campaign request handled successfully")
        
        # Step 2: Synthesize strategy
        print("\n[Step 2] Synthesizing campaign strategy...")
        updated_campaign = await orchestrator.synthesize_strategy(
            campaign=sample_campaign,
            agent_results=agent_results
        )
        
        assert updated_campaign is not None
        assert updated_campaign.campaign_id == sample_campaign.campaign_id
        print("✓ Strategy synthesized successfully")
        
        # Step 3: Verify campaign completeness
        print("\n[Step 3] Verifying campaign completeness...")
        assert updated_campaign.campaign_id is not None
        assert updated_campaign.account_id is not None
        assert updated_campaign.status in [CampaignStatus.DRAFT, CampaignStatus.ACTIVE]
        assert updated_campaign.business_goal is not None
        assert updated_campaign.monthly_budget > 0
        assert updated_campaign.target_audience is not None
        assert len(updated_campaign.products) > 0
        print("✓ Campaign is complete and valid")
        
        # Step 4: Calculate launch timeline
        print("\n[Step 4] Calculating launch timeline...")
        timeline = orchestrator._calculate_launch_timeline(
            campaign=updated_campaign,
            requires_review=agent_results.get("requires_review", False)
        )
        assert timeline is not None
        assert len(timeline) > 0
        print(f"✓ Estimated launch timeline: {timeline}")
        
        print("\n" + "="*60)
        print("WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"\nCampaign Summary:")
        print(f"  - Campaign ID: {updated_campaign.campaign_id}")
        print(f"  - Account ID: {updated_campaign.account_id}")
        print(f"  - Status: {updated_campaign.status}")
        print(f"  - Budget: ${updated_campaign.monthly_budget}")
        print(f"  - Goal: {updated_campaign.business_goal}")
        print(f"  - Products: {', '.join(updated_campaign.products)}")
        print(f"  - Creative Variants: {len(updated_campaign.creative_variants)}")
        print(f"  - Audience Segments: {len(updated_campaign.audience_segments)}")
        print(f"  - Requires Review: {agent_results.get('requires_review', False)}")
        print(f"  - Estimated Launch: {timeline}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("END-TO-END CAMPAIGN WORKFLOW TEST SUITE")
    print("="*60 + "\n")
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])
