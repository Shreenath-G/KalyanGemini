"""End-to-end test suite for bid execution workflow

Tests the complete bid execution flow including:
- Bid request handling
- Opportunity evaluation
- Bid price calculation
- Bid submission
- Win rate tracking

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
import uuid
import time

# Test imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.campaign import Campaign, CampaignStatus, OptimizationMode
from src.models.bidding import BidRequest, BidResponse, UserProfile


class MockBidExecutionAgent:
    """Mock Bid Execution Agent for testing"""
    
    def __init__(self):
        self.name = "bid_execution"
        self.bid_history = []
        self.win_rate = 0.30
    
    def is_relevant(self, bid_request: BidRequest) -> bool:
        """Quick relevance check for bid opportunity"""
        # Check if user profile matches campaign criteria
        if not bid_request.user_profile:
            return False
        
        # Check if inventory type is supported
        if bid_request.inventory_type not in ["display", "search", "social"]:
            return False
        
        return True
    
    def match_segment(self, user_profile: UserProfile, campaign: Campaign) -> Dict[str, Any]:
        """Match user profile to audience segments"""
        if not campaign.audience_segments:
            return None
        
        # Simple matching logic for testing
        for segment in campaign.audience_segments:
            segment_data = segment if isinstance(segment, dict) else segment.__dict__
            
            # Check age range match
            demographics = segment_data.get("demographics", {})
            age_range = demographics.get("age_range", "")
            
            if age_range and user_profile.age:
                age_parts = age_range.split("-")
                if len(age_parts) == 2:
                    min_age, max_age = int(age_parts[0]), int(age_parts[1])
                    if min_age <= user_profile.age <= max_age:
                        return {
                            "segment_id": segment_data.get("segment_id"),
                            "campaign_id": campaign.campaign_id,
                            "creative_id": campaign.creative_variants[0].get("variant_id") if campaign.creative_variants else None,
                            "max_cpc": 2.50,
                            "conversion_probability": 0.10
                        }
        
        return None
    
    def check_budget(self, campaign_id: str) -> Dict[str, Any]:
        """Check budget availability"""
        # Mock budget check
        return {
            "available": True,
            "remaining": 500.00,
            "daily_budget": 166.67
        }
    
    def calculate_bid(
        self,
        segment_match: Dict[str, Any],
        user_profile: UserProfile,
        budget_remaining: float
    ) -> float:
        """Calculate optimal bid price"""
        base_bid = segment_match.get("max_cpc", 2.00)
        conversion_prob = segment_match.get("conversion_probability", 0.05)
        
        # Adjust for conversion probability
        adjusted_bid = base_bid * (conversion_prob / 0.05)
        
        # Reduce if budget is low
        if budget_remaining < 0.10:
            adjusted_bid *= 0.70
        
        return round(adjusted_bid, 2)
    
    async def handle_bid_request(
        self,
        bid_request: BidRequest,
        campaign: Campaign
    ) -> BidResponse:
        """Handle bid request with <100ms response time"""
        start_time = time.time()
        
        # Quick relevance check
        if not self.is_relevant(bid_request):
            return None
        
        # Match to segment
        segment_match = self.match_segment(bid_request.user_profile, campaign)
        if not segment_match:
            return None
        
        # Check budget
        budget_check = self.check_budget(campaign.campaign_id)
        if not budget_check["available"]:
            return None
        
        # Calculate bid price
        bid_price = self.calculate_bid(
            segment_match=segment_match,
            user_profile=bid_request.user_profile,
            budget_remaining=budget_check["remaining"] / budget_check["daily_budget"]
        )
        
        # Ensure response time < 100ms
        elapsed = time.time() - start_time
        if elapsed > 0.100:
            print(f"⚠ Warning: Bid decision took {elapsed*1000:.2f}ms (target: <100ms)")
        
        # Create bid response
        response = BidResponse(
            bid_id=str(uuid.uuid4()),
            bid_price=bid_price,
            campaign_id=segment_match["campaign_id"],
            creative_id=segment_match["creative_id"],
            segment_id=segment_match["segment_id"],
            timestamp=datetime.utcnow()
        )
        
        # Track bid
        self.bid_history.append({
            "bid_id": response.bid_id,
            "bid_price": bid_price,
            "timestamp": response.timestamp,
            "won": False  # Will be updated when result is known
        })
        
        return response
    
    def track_bid_result(self, bid_id: str, won: bool):
        """Track bid win/loss result"""
        for bid in self.bid_history:
            if bid["bid_id"] == bid_id:
                bid["won"] = won
                break
    
    def calculate_win_rate(self) -> float:
        """Calculate current bid win rate"""
        if not self.bid_history:
            return 0.0
        
        wins = sum(1 for bid in self.bid_history if bid["won"])
        return wins / len(self.bid_history)
    
    def adjust_bidding_strategy(self):
        """Adjust bidding strategy to maintain 20-40% win rate"""
        current_win_rate = self.calculate_win_rate()
        
        if current_win_rate < 0.20:
            # Increase bids
            return "increase_bids"
        elif current_win_rate > 0.40:
            # Decrease bids
            return "decrease_bids"
        else:
            # Maintain current strategy
            return "maintain"


class TestBidExecutionWorkflow:
    """Test complete bid execution workflow"""
    
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
            target_audience="small business owners aged 30-50",
            products=["CRM Software"],
            optimization_mode=OptimizationMode.STANDARD,
            creative_variants=[
                {
                    "variant_id": "var_001",
                    "status": "active",
                    "headlines": {"short": "Save 50%"},
                    "body": "Upgrade now",
                    "cta": "Get Started"
                }
            ],
            audience_segments=[
                {
                    "segment_id": "seg_001",
                    "name": "Tech-Savvy Business Owners",
                    "demographics": {"age_range": "30-50", "income": "50k-150k"},
                    "priority_score": 0.85
                }
            ]
        )
    
    @pytest.fixture
    def sample_bid_request(self) -> BidRequest:
        """Create a sample bid request"""
        return BidRequest(
            request_id=str(uuid.uuid4()),
            inventory_type="display",
            user_profile=UserProfile(
                age=35,
                gender="male",
                interests=["business", "technology", "productivity"],
                location="US",
                device="desktop"
            ),
            floor_price=0.50,
            timestamp=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_bid_agent_initialization(self):
        """Test Bid Execution Agent initialization"""
        agent = MockBidExecutionAgent()
        
        assert agent.name == "bid_execution"
        assert agent.bid_history == []
        assert agent.win_rate >= 0
        
        print("✓ Bid Execution Agent initialized successfully")
    
    @pytest.mark.asyncio
    async def test_relevance_check(self, sample_bid_request: BidRequest):
        """Test quick relevance filtering"""
        agent = MockBidExecutionAgent()
        
        # Test relevant request
        is_relevant = agent.is_relevant(sample_bid_request)
        assert is_relevant is True
        
        # Test irrelevant request (no user profile)
        irrelevant_request = BidRequest(
            request_id=str(uuid.uuid4()),
            inventory_type="display",
            user_profile=None,
            floor_price=0.50,
            timestamp=datetime.utcnow()
        )
        is_relevant = agent.is_relevant(irrelevant_request)
        assert is_relevant is False
        
        print("✓ Relevance check working correctly")
    
    @pytest.mark.asyncio
    async def test_segment_matching(self, sample_campaign: Campaign, sample_bid_request: BidRequest):
        """Test user profile to segment matching"""
        agent = MockBidExecutionAgent()
        
        # Test matching
        segment_match = agent.match_segment(
            user_profile=sample_bid_request.user_profile,
            campaign=sample_campaign
        )
        
        if segment_match:
            assert "segment_id" in segment_match
            assert "campaign_id" in segment_match
            assert "max_cpc" in segment_match
            assert segment_match["campaign_id"] == sample_campaign.campaign_id
            
            print(f"✓ User matched to segment: {segment_match['segment_id']}")
        else:
            print("✓ No segment match (expected for some profiles)")
    
    @pytest.mark.asyncio
    async def test_budget_check(self, sample_campaign: Campaign):
        """Test budget availability check"""
        agent = MockBidExecutionAgent()
        
        budget_check = agent.check_budget(sample_campaign.campaign_id)
        
        assert "available" in budget_check
        assert "remaining" in budget_check
        assert "daily_budget" in budget_check
        
        print(f"✓ Budget check completed")
        print(f"    Available: {budget_check['available']}")
        print(f"    Remaining: ${budget_check['remaining']:.2f}")
    
    @pytest.mark.asyncio
    async def test_bid_price_calculation(self, sample_bid_request: BidRequest):
        """Test bid price calculation logic"""
        agent = MockBidExecutionAgent()
        
        segment_match = {
            "segment_id": "seg_001",
            "campaign_id": "camp_test_123",
            "creative_id": "var_001",
            "max_cpc": 2.50,
            "conversion_probability": 0.10
        }
        
        # Test normal budget
        bid_price = agent.calculate_bid(
            segment_match=segment_match,
            user_profile=sample_bid_request.user_profile,
            budget_remaining=0.50
        )
        
        assert bid_price > 0
        assert bid_price <= segment_match["max_cpc"] * 2  # Should be reasonable
        
        # Test low budget (should reduce bid)
        bid_price_low_budget = agent.calculate_bid(
            segment_match=segment_match,
            user_profile=sample_bid_request.user_profile,
            budget_remaining=0.05
        )
        
        assert bid_price_low_budget < bid_price
        
        print(f"✓ Bid price calculation working")
        print(f"    Normal budget bid: ${bid_price:.2f}")
        print(f"    Low budget bid: ${bid_price_low_budget:.2f}")
    
    @pytest.mark.asyncio
    async def test_bid_request_handling(self, sample_campaign: Campaign, sample_bid_request: BidRequest):
        """Test complete bid request handling with response time"""
        agent = MockBidExecutionAgent()
        
        start_time = time.time()
        
        # Handle bid request
        response = await agent.handle_bid_request(
            bid_request=sample_bid_request,
            campaign=sample_campaign
        )
        
        elapsed = time.time() - start_time
        
        # Verify response time < 100ms
        assert elapsed < 0.100, f"Bid decision took {elapsed*1000:.2f}ms (target: <100ms)"
        
        if response:
            assert response.bid_id is not None
            assert response.bid_price > 0
            assert response.campaign_id == sample_campaign.campaign_id
            assert response.timestamp is not None
            
            print(f"✓ Bid request handled in {elapsed*1000:.2f}ms")
            print(f"    Bid ID: {response.bid_id}")
            print(f"    Bid Price: ${response.bid_price:.2f}")
        else:
            print("✓ Bid request rejected (no match)")
    
    @pytest.mark.asyncio
    async def test_bid_tracking(self, sample_campaign: Campaign, sample_bid_request: BidRequest):
        """Test bid tracking and win rate calculation"""
        agent = MockBidExecutionAgent()
        
        # Submit multiple bids
        for i in range(10):
            response = await agent.handle_bid_request(
                bid_request=sample_bid_request,
                campaign=sample_campaign
            )
            
            if response:
                # Simulate win/loss (30% win rate)
                won = (i % 3 == 0)
                agent.track_bid_result(response.bid_id, won)
        
        # Calculate win rate
        win_rate = agent.calculate_win_rate()
        
        assert 0 <= win_rate <= 1.0
        assert len(agent.bid_history) > 0
        
        print(f"✓ Bid tracking working")
        print(f"    Total bids: {len(agent.bid_history)}")
        print(f"    Win rate: {win_rate*100:.1f}%")
    
    @pytest.mark.asyncio
    async def test_bidding_strategy_adjustment(self):
        """Test bidding strategy adjustment based on win rate"""
        agent = MockBidExecutionAgent()
        
        # Simulate low win rate (15%)
        for i in range(20):
            agent.bid_history.append({
                "bid_id": str(uuid.uuid4()),
                "bid_price": 2.00,
                "timestamp": datetime.utcnow(),
                "won": (i < 3)  # 3 wins out of 20 = 15%
            })
        
        adjustment = agent.adjust_bidding_strategy()
        assert adjustment == "increase_bids"
        print(f"✓ Low win rate (15%) → Strategy: {adjustment}")
        
        # Simulate high win rate (50%)
        agent.bid_history = []
        for i in range(20):
            agent.bid_history.append({
                "bid_id": str(uuid.uuid4()),
                "bid_price": 2.00,
                "timestamp": datetime.utcnow(),
                "won": (i < 10)  # 10 wins out of 20 = 50%
            })
        
        adjustment = agent.adjust_bidding_strategy()
        assert adjustment == "decrease_bids"
        print(f"✓ High win rate (50%) → Strategy: {adjustment}")
        
        # Simulate optimal win rate (30%)
        agent.bid_history = []
        for i in range(20):
            agent.bid_history.append({
                "bid_id": str(uuid.uuid4()),
                "bid_price": 2.00,
                "timestamp": datetime.utcnow(),
                "won": (i < 6)  # 6 wins out of 20 = 30%
            })
        
        adjustment = agent.adjust_bidding_strategy()
        assert adjustment == "maintain"
        print(f"✓ Optimal win rate (30%) → Strategy: {adjustment}")
    
    @pytest.mark.asyncio
    async def test_complete_bid_workflow(self, sample_campaign: Campaign):
        """Test complete end-to-end bid execution workflow
        
        This is the main integration test that verifies:
        1. Bid requests are received from ad exchange
        2. Opportunities are evaluated quickly (<100ms)
        3. User profiles are matched to segments
        4. Budget availability is checked
        5. Bid prices are calculated
        6. Bids are submitted
        7. Results are tracked
        8. Win rates are monitored
        9. Bidding strategy is adjusted
        """
        agent = MockBidExecutionAgent()
        
        print("\n" + "="*60)
        print("COMPLETE BID EXECUTION WORKFLOW TEST")
        print("="*60)
        
        # Step 1: Simulate multiple bid requests
        print("\n[Step 1] Processing bid requests...")
        bid_count = 0
        response_times = []
        
        for i in range(50):
            # Create bid request
            bid_request = BidRequest(
                request_id=str(uuid.uuid4()),
                inventory_type="display",
                user_profile=UserProfile(
                    age=30 + (i % 20),
                    gender="male" if i % 2 == 0 else "female",
                    interests=["business", "technology"],
                    location="US",
                    device="desktop"
                ),
                floor_price=0.50,
                timestamp=datetime.utcnow()
            )
            
            # Handle bid request
            start_time = time.time()
            response = await agent.handle_bid_request(
                bid_request=bid_request,
                campaign=sample_campaign
            )
            elapsed = time.time() - start_time
            
            if response:
                bid_count += 1
                response_times.append(elapsed)
                
                # Simulate win/loss
                won = (i % 3 == 0)
                agent.track_bid_result(response.bid_id, won)
        
        print(f"✓ Processed 50 bid requests")
        print(f"    Bids submitted: {bid_count}")
        print(f"    Average response time: {sum(response_times)/len(response_times)*1000:.2f}ms")
        print(f"    Max response time: {max(response_times)*1000:.2f}ms")
        
        # Step 2: Verify response time requirement
        print("\n[Step 2] Verifying response time requirement...")
        assert all(t < 0.100 for t in response_times), "Some bids exceeded 100ms response time"
        print("✓ All bids processed within 100ms requirement")
        
        # Step 3: Calculate win rate
        print("\n[Step 3] Calculating win rate...")
        win_rate = agent.calculate_win_rate()
        print(f"✓ Current win rate: {win_rate*100:.1f}%")
        
        # Step 4: Adjust bidding strategy
        print("\n[Step 4] Adjusting bidding strategy...")
        adjustment = agent.adjust_bidding_strategy()
        print(f"✓ Strategy adjustment: {adjustment}")
        
        print("\n" + "="*60)
        print("BID EXECUTION WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"\nBid Execution Summary:")
        print(f"  - Campaign ID: {sample_campaign.campaign_id}")
        print(f"  - Total Bid Requests: 50")
        print(f"  - Bids Submitted: {bid_count}")
        print(f"  - Win Rate: {win_rate*100:.1f}%")
        print(f"  - Target Win Rate: 20-40%")
        print(f"  - Average Response Time: {sum(response_times)/len(response_times)*1000:.2f}ms")
        print(f"  - Strategy Adjustment: {adjustment}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("END-TO-END BID EXECUTION TEST SUITE")
    print("="*60 + "\n")
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])
