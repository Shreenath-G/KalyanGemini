"""Bid Execution Agent - Executes real-time programmatic bidding decisions"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.models.bidding import (
    BidRequest,
    BidResponse,
    NoBidResponse,
    BidDecision,
    SegmentMatch,
    BudgetCheck,
    BiddingStrategy,
    BidRequestStatus
)
from src.models.audience import AudienceSegment
from src.models.campaign import Campaign, CampaignStatus
from src.services.firestore import get_firestore_service
from src.config import settings

logger = logging.getLogger(__name__)


class AgentMessage:
    """Message structure for agent communication"""
    
    def __init__(
        self,
        message_type: str,
        data: Dict[str, Any],
        sender: str = "bid_execution",
        correlation_id: Optional[str] = None
    ):
        self.message_type = message_type
        self.data = data
        self.sender = sender
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_type": self.message_type,
            "data": self.data,
            "sender": self.sender,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat()
        }


class BidExecutionAgent:
    """
    Bid Execution Agent
    
    Executes real-time programmatic bidding decisions by:
    - Receiving bid requests from ad exchanges via webhook
    - Evaluating opportunities in <100ms
    - Matching user profiles to audience segments
    - Checking budget availability
    - Calculating optimal bid prices
    - Tracking bid decisions and win rates
    - Adjusting bidding strategy to maintain 20-40% win rate
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 11.1, 11.2
    """
    
    def __init__(self):
        """Initialize the Bid Execution Agent"""
        self.name = "bid_execution"
        self.firestore_service = get_firestore_service()
        
        # Performance thresholds
        self.max_response_time_ms = 100  # Maximum response time
        self.target_response_time_ms = 50  # Target for evaluation logic
        self.min_conversion_probability = 0.05  # Minimum to bid
        self.budget_low_threshold = 0.10  # 10% remaining
        self.budget_reduction_factor = 0.70  # 30% reduction when low
        
        # Win rate targets
        self.target_win_rate_min = 0.20
        self.target_win_rate_max = 0.40
        self.target_win_rate = 0.30
        
        # Cache for active campaigns and segments (refreshed periodically)
        self._campaign_cache: Dict[str, Campaign] = {}
        self._segment_cache: Dict[str, List[AudienceSegment]] = {}
        self._strategy_cache: Dict[str, BiddingStrategy] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_refresh = datetime.utcnow()
        
        logger.info(
            f"Bid Execution Agent initialized",
            extra={
                "agent_name": self.name,
                "max_response_time_ms": self.max_response_time_ms,
                "min_conversion_probability": self.min_conversion_probability,
                "target_win_rate": self.target_win_rate
            }
        )
    
    async def handle_bid_request(self, bid_request: BidRequest) -> BidResponse | NoBidResponse:
        """
        Handle incoming bid request from ad exchange
        
        This is the main entry point for real-time bidding. Must respond
        within 100ms to be competitive in programmatic auctions.
        
        Process:
        1. Quick relevance check (<10ms)
        2. Match user to audience segments (<20ms)
        3. Check budget availability (<10ms)
        4. Calculate bid price (<10ms)
        5. Return bid response (<50ms total)
        
        Args:
            bid_request: Bid request from ad exchange
            
        Returns:
            BidResponse with bid price or NoBidResponse if not bidding
            
        Requirements: 7.1, 11.1, 11.2
        """
        start_time = time.time()
        request_id = bid_request.request_id
        
        logger.debug(
            f"Handling bid request",
            extra={
                "request_id": request_id,
                "user_id": bid_request.user_profile.user_id,
                "inventory_id": bid_request.inventory.inventory_id,
                "floor_price": bid_request.inventory.floor_price
            }
        )
        
        try:
            # Step 1: Quick relevance check
            if not self.is_relevant(bid_request):
                elapsed_ms = (time.time() - start_time) * 1000
                await self._log_bid_decision(
                    bid_request=bid_request,
                    decision="no_bid",
                    reason="Not relevant to active campaigns",
                    processing_time_ms=elapsed_ms
                )
                return NoBidResponse(
                    request_id=request_id,
                    reason="Not relevant to active campaigns"
                )
            
            # Step 2: Match user to audience segments
            segment_match = await self.match_segment(bid_request.user_profile)
            
            if not segment_match:
                elapsed_ms = (time.time() - start_time) * 1000
                await self._log_bid_decision(
                    bid_request=bid_request,
                    decision="no_bid",
                    reason="No matching audience segments",
                    processing_time_ms=elapsed_ms
                )
                return NoBidResponse(
                    request_id=request_id,
                    reason="No matching audience segments"
                )
            
            # Step 3: Check budget availability
            budget_check = await self.check_budget(segment_match.campaign_id)
            
            if not budget_check.available:
                elapsed_ms = (time.time() - start_time) * 1000
                await self._log_bid_decision(
                    bid_request=bid_request,
                    decision="no_bid",
                    reason="Budget exhausted",
                    processing_time_ms=elapsed_ms,
                    campaign_id=segment_match.campaign_id,
                    segment_id=segment_match.segment_id
                )
                return NoBidResponse(
                    request_id=request_id,
                    reason="Budget exhausted"
                )
            
            # Step 4: Calculate bid price
            bid_price = self.calculate_bid(
                segment=segment_match,
                user_profile=bid_request.user_profile,
                budget_check=budget_check,
                floor_price=bid_request.inventory.floor_price
            )
            
            # Check if bid meets floor price
            if bid_price < bid_request.inventory.floor_price:
                elapsed_ms = (time.time() - start_time) * 1000
                await self._log_bid_decision(
                    bid_request=bid_request,
                    decision="no_bid",
                    reason=f"Bid price ${bid_price:.2f} below floor ${bid_request.inventory.floor_price:.2f}",
                    processing_time_ms=elapsed_ms,
                    campaign_id=segment_match.campaign_id,
                    segment_id=segment_match.segment_id
                )
                return NoBidResponse(
                    request_id=request_id,
                    reason="Bid below floor price"
                )
            
            # Step 5: Create bid response
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Log warning if we're approaching timeout
            if elapsed_ms > 80:
                logger.warning(
                    f"Bid decision took longer than expected",
                    extra={
                        "request_id": request_id,
                        "processing_time_ms": elapsed_ms,
                        "threshold_ms": self.max_response_time_ms
                    }
                )
            
            # Log bid decision
            await self._log_bid_decision(
                bid_request=bid_request,
                decision="bid",
                reason=f"Match score: {segment_match.match_score:.2f}, Conv prob: {segment_match.conversion_probability:.2f}",
                processing_time_ms=elapsed_ms,
                campaign_id=segment_match.campaign_id,
                segment_id=segment_match.segment_id,
                creative_id=segment_match.creative_id,
                bid_price=bid_price,
                user_conversion_probability=segment_match.conversion_probability,
                segment_max_cpc=segment_match.max_cpc,
                budget_remaining_percent=budget_check.remaining_percent
            )
            
            logger.info(
                f"Bid submitted",
                extra={
                    "request_id": request_id,
                    "campaign_id": segment_match.campaign_id,
                    "bid_price": bid_price,
                    "processing_time_ms": elapsed_ms
                }
            )
            
            return BidResponse(
                request_id=request_id,
                bid_price=bid_price,
                campaign_id=segment_match.campaign_id,
                creative_id=segment_match.creative_id,
                segment_id=segment_match.segment_id
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Error handling bid request",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": elapsed_ms
                }
            )
            return NoBidResponse(
                request_id=request_id,
                reason="Internal error"
            )


# Global agent instance
_agent_instance: Optional[BidExecutionAgent] = None


def get_bid_execution_agent() -> BidExecutionAgent:
    """Get or create the global Bid Execution Agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = BidExecutionAgent()
    return _agent_instance

    def is_relevant(self, bid_request: BidRequest) -> bool:
        """
        Quick relevance check for bid opportunity
        
        Filters out obviously irrelevant requests to save processing time.
        This should complete in <10ms.
        
        Checks:
        - Platform is supported (google, meta, programmatic)
        - Placement type is supported
        - Floor price is reasonable
        - We have active campaigns
        
        Args:
            bid_request: Bid request to evaluate
            
        Returns:
            True if relevant, False otherwise
            
        Requirements: 7.2, 7.3
        """
        # Check if platform is supported
        supported_platforms = ["google", "meta", "programmatic"]
        if bid_request.inventory.platform not in supported_platforms:
            logger.debug(
                f"Unsupported platform",
                extra={
                    "request_id": bid_request.request_id,
                    "platform": bid_request.inventory.platform
                }
            )
            return False
        
        # Check if floor price is reasonable (not too high)
        max_floor_price = 15.00  # Maximum floor price we'll consider
        if bid_request.inventory.floor_price > max_floor_price:
            logger.debug(
                f"Floor price too high",
                extra={
                    "request_id": bid_request.request_id,
                    "floor_price": bid_request.inventory.floor_price,
                    "max_floor_price": max_floor_price
                }
            )
            return False
        
        # Check if we have any active campaigns (use cache)
        if not self._campaign_cache:
            # Cache is empty, might need refresh but don't block
            logger.debug(
                f"No active campaigns in cache",
                extra={"request_id": bid_request.request_id}
            )
            return False
        
        return True
    
    async def match_segment(self, user_profile) -> Optional[SegmentMatch]:
        """
        Match user profile to audience segments
        
        Finds the best matching audience segment for the user based on:
        - Demographics (age, gender, location)
        - Interests
        - Behaviors
        - Device type
        
        Returns the segment with highest match score and conversion probability.
        This should complete in <20ms.
        
        Args:
            user_profile: User profile from bid request
            
        Returns:
            SegmentMatch if found, None otherwise
            
        Requirements: 7.2, 7.3
        """
        # Refresh cache if needed
        await self._refresh_cache_if_needed()
        
        best_match: Optional[SegmentMatch] = None
        best_score = 0.0
        
        # Iterate through all active campaigns and their segments
        for campaign_id, campaign in self._campaign_cache.items():
            # Skip if campaign is not active
            if campaign.status != CampaignStatus.ACTIVE:
                continue
            
            # Get segments for this campaign
            segments = self._segment_cache.get(campaign_id, [])
            
            for segment in segments:
                # Calculate match score
                match_score = self._calculate_match_score(user_profile, segment)
                
                # Only consider if match score is above threshold
                if match_score >= 0.5 and match_score > best_score:
                    # Get budget allocation to find max CPC
                    allocation = await self.firestore_service.get_allocation(campaign_id)
                    if not allocation:
                        continue
                    
                    # Find segment allocation
                    segment_alloc = next(
                        (a for a in allocation.allocations if a.segment_id == segment.segment_id),
                        None
                    )
                    
                    if not segment_alloc:
                        continue
                    
                    # Get a creative variant for this campaign
                    variants = await self.firestore_service.get_variants_by_campaign(campaign_id)
                    if not variants:
                        continue
                    
                    # Use first active variant (could be more sophisticated)
                    active_variant = next(
                        (v for v in variants if v.status == "active"),
                        variants[0] if variants else None
                    )
                    
                    if not active_variant:
                        continue
                    
                    # Estimate conversion probability based on segment and match
                    conversion_probability = segment.conversion_probability * match_score
                    
                    # Only bid if conversion probability is above minimum
                    if conversion_probability >= self.min_conversion_probability:
                        best_score = match_score
                        best_match = SegmentMatch(
                            campaign_id=campaign_id,
                            segment_id=segment.segment_id,
                            creative_id=active_variant.variant_id,
                            max_cpc=segment_alloc.max_cpc,
                            match_score=match_score,
                            conversion_probability=conversion_probability
                        )
        
        if best_match:
            logger.debug(
                f"Found segment match",
                extra={
                    "campaign_id": best_match.campaign_id,
                    "segment_id": best_match.segment_id,
                    "match_score": best_match.match_score,
                    "conversion_probability": best_match.conversion_probability
                }
            )
        else:
            logger.debug("No segment match found")
        
        return best_match
    
    def _calculate_match_score(self, user_profile, segment: AudienceSegment) -> float:
        """
        Calculate match score between user profile and segment
        
        Scoring factors:
        - Demographics match: 40%
        - Interests overlap: 30%
        - Behaviors overlap: 30%
        
        Args:
            user_profile: User profile from bid request
            segment: Audience segment
            
        Returns:
            Match score between 0.0 and 1.0
        """
        score = 0.0
        
        # Demographics match (40%)
        demographics_score = 0.0
        user_demo = user_profile.demographics
        segment_demo = segment.demographics
        
        # Age range match
        if user_demo.get("age_range") and segment_demo.get("age_range"):
            if user_demo["age_range"] == segment_demo["age_range"]:
                demographics_score += 0.5
            # Partial match for adjacent ranges
            elif self._age_ranges_adjacent(user_demo["age_range"], segment_demo["age_range"]):
                demographics_score += 0.25
        
        # Gender match
        if segment_demo.get("gender") == "all":
            demographics_score += 0.5
        elif user_demo.get("gender") and segment_demo.get("gender"):
            if user_demo["gender"] == segment_demo["gender"]:
                demographics_score += 0.5
        
        score += demographics_score * 0.4
        
        # Interests overlap (30%)
        user_interests = set(user_profile.interests)
        segment_interests = set(segment.interests)
        
        if user_interests and segment_interests:
            interests_overlap = len(user_interests & segment_interests) / len(segment_interests)
            score += interests_overlap * 0.3
        
        # Behaviors overlap (30%)
        user_behaviors = set(user_profile.behaviors)
        segment_behaviors = set(segment.behaviors)
        
        if user_behaviors and segment_behaviors:
            behaviors_overlap = len(user_behaviors & segment_behaviors) / len(segment_behaviors)
            score += behaviors_overlap * 0.3
        
        return min(1.0, score)
    
    def _age_ranges_adjacent(self, range1: str, range2: str) -> bool:
        """Check if two age ranges are adjacent"""
        age_order = ["18-24", "25-34", "30-45", "35-50", "45-60", "50-65", "60+"]
        try:
            idx1 = age_order.index(range1)
            idx2 = age_order.index(range2)
            return abs(idx1 - idx2) == 1
        except ValueError:
            return False
    
    async def check_budget(self, campaign_id: str) -> BudgetCheck:
        """
        Check budget availability for a campaign
        
        Verifies that the campaign has sufficient budget remaining
        to place a bid. This should complete in <10ms using cached data.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            BudgetCheck with availability and remaining budget
            
        Requirements: 7.2, 7.3
        """
        try:
            # Get budget allocation from Firestore
            allocation = await self.firestore_service.get_allocation(campaign_id)
            
            if not allocation:
                logger.warning(
                    f"No budget allocation found",
                    extra={"campaign_id": campaign_id}
                )
                return BudgetCheck(
                    campaign_id=campaign_id,
                    available=False,
                    remaining=0.0,
                    remaining_percent=0.0,
                    daily_budget=0.0,
                    current_spend=0.0
                )
            
            # Calculate remaining budget
            remaining = allocation.remaining_budget
            remaining_percent = (remaining / allocation.total_budget) * 100 if allocation.total_budget > 0 else 0.0
            
            # Check if budget is available (at least $1 remaining)
            available = remaining >= 1.0
            
            logger.debug(
                f"Budget check",
                extra={
                    "campaign_id": campaign_id,
                    "available": available,
                    "remaining": remaining,
                    "remaining_percent": remaining_percent,
                    "daily_budget": allocation.daily_budget,
                    "total_spent": allocation.total_spent
                }
            )
            
            return BudgetCheck(
                campaign_id=campaign_id,
                available=available,
                remaining=remaining,
                remaining_percent=remaining_percent,
                daily_budget=allocation.daily_budget,
                current_spend=allocation.total_spent
            )
            
        except Exception as e:
            logger.error(
                f"Error checking budget",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
            # Fail-safe: return unavailable
            return BudgetCheck(
                campaign_id=campaign_id,
                available=False,
                remaining=0.0,
                remaining_percent=0.0,
                daily_budget=0.0,
                current_spend=0.0
            )
    
    async def _refresh_cache_if_needed(self) -> None:
        """
        Refresh campaign and segment cache if TTL expired
        
        Cache is refreshed every 5 minutes to balance performance
        and data freshness.
        """
        now = datetime.utcnow()
        elapsed = (now - self._last_cache_refresh).total_seconds()
        
        if elapsed < self._cache_ttl:
            return
        
        logger.info("Refreshing campaign and segment cache")
        
        try:
            # Get all active campaigns
            campaigns = await self.firestore_service.get_active_campaigns()
            
            # Update campaign cache
            self._campaign_cache = {c.campaign_id: c for c in campaigns}
            
            # Update segment cache
            for campaign in campaigns:
                segments = await self.firestore_service.get_segments_by_campaign(campaign.campaign_id)
                self._segment_cache[campaign.campaign_id] = segments
            
            # Update strategy cache
            for campaign_id in self._campaign_cache.keys():
                strategy = await self._get_bidding_strategy(campaign_id)
                if strategy:
                    self._strategy_cache[campaign_id] = strategy
            
            self._last_cache_refresh = now
            
            logger.info(
                f"Cache refreshed",
                extra={
                    "campaign_count": len(self._campaign_cache),
                    "segment_count": sum(len(s) for s in self._segment_cache.values())
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error refreshing cache",
                extra={"error": str(e)}
            )

    def calculate_bid(
        self,
        segment: SegmentMatch,
        user_profile,
        budget_check: BudgetCheck,
        floor_price: float
    ) -> float:
        """
        Calculate optimal bid price for the opportunity
        
        Bid calculation formula:
        1. Start with segment max CPC
        2. Adjust for user conversion probability
        3. Adjust for remaining budget (reduce when low)
        4. Apply bidding strategy adjustment factor
        5. Ensure bid is above floor price
        
        Args:
            segment: Matched segment with max CPC
            user_profile: User profile from bid request
            budget_check: Budget availability check result
            floor_price: Minimum bid price from exchange
            
        Returns:
            Calculated bid price in USD
            
        Requirements: 7.2, 7.4
        """
        # Start with segment max CPC
        base_bid = segment.max_cpc
        
        # Adjust for user conversion probability
        # Higher conversion probability = higher bid
        conversion_multiplier = 0.5 + (segment.conversion_probability * 1.0)
        adjusted_bid = base_bid * conversion_multiplier
        
        # Adjust for remaining budget
        # If budget is low (<10%), reduce bids by 30% to extend reach
        if budget_check.remaining_percent < (self.budget_low_threshold * 100):
            adjusted_bid *= self.budget_reduction_factor
            logger.debug(
                f"Reducing bid due to low budget",
                extra={
                    "campaign_id": segment.campaign_id,
                    "remaining_percent": budget_check.remaining_percent,
                    "reduction_factor": self.budget_reduction_factor,
                    "original_bid": base_bid * conversion_multiplier,
                    "adjusted_bid": adjusted_bid
                }
            )
        
        # Apply bidding strategy adjustment factor
        strategy = self._strategy_cache.get(segment.campaign_id)
        if strategy:
            adjusted_bid *= strategy.bid_adjustment_factor
            logger.debug(
                f"Applied strategy adjustment",
                extra={
                    "campaign_id": segment.campaign_id,
                    "adjustment_factor": strategy.bid_adjustment_factor,
                    "current_win_rate": strategy.current_win_rate,
                    "target_win_rate": strategy.target_win_rate
                }
            )
        
        # Ensure bid is at least the floor price
        final_bid = max(floor_price, adjusted_bid)
        
        # Cap at reasonable maximum (2x segment max CPC)
        max_bid = segment.max_cpc * 2.0
        final_bid = min(final_bid, max_bid)
        
        # Round to 2 decimal places
        final_bid = round(final_bid, 2)
        
        logger.debug(
            f"Calculated bid price",
            extra={
                "campaign_id": segment.campaign_id,
                "segment_id": segment.segment_id,
                "base_bid": base_bid,
                "conversion_probability": segment.conversion_probability,
                "conversion_multiplier": conversion_multiplier,
                "budget_remaining_percent": budget_check.remaining_percent,
                "floor_price": floor_price,
                "final_bid": final_bid
            }
        )
        
        return final_bid
    
    async def _log_bid_decision(
        self,
        bid_request: BidRequest,
        decision: str,
        reason: str,
        processing_time_ms: float,
        campaign_id: Optional[str] = None,
        segment_id: Optional[str] = None,
        creative_id: Optional[str] = None,
        bid_price: Optional[float] = None,
        user_conversion_probability: Optional[float] = None,
        segment_max_cpc: Optional[float] = None,
        budget_remaining_percent: Optional[float] = None
    ) -> None:
        """
        Log bid decision to Firestore for tracking and analysis
        
        Args:
            bid_request: Original bid request
            decision: "bid" or "no_bid"
            reason: Reason for decision
            processing_time_ms: Processing time in milliseconds
            campaign_id: Campaign ID if matched
            segment_id: Segment ID if matched
            creative_id: Creative ID if matched
            bid_price: Bid price if bidding
            user_conversion_probability: Estimated conversion probability
            segment_max_cpc: Segment max CPC
            budget_remaining_percent: Remaining budget percentage
        """
        try:
            bid_decision = BidDecision(
                request_id=bid_request.request_id,
                campaign_id=campaign_id,
                segment_id=segment_id,
                creative_id=creative_id,
                bid_price=bid_price,
                decision=decision,
                reason=reason,
                status=BidRequestStatus.SUBMITTED if decision == "bid" else BidRequestStatus.REJECTED,
                processing_time_ms=processing_time_ms,
                user_conversion_probability=user_conversion_probability,
                segment_max_cpc=segment_max_cpc,
                budget_remaining_percent=budget_remaining_percent
            )
            
            # Store in Firestore
            await self.firestore_service.log_bid_decision(bid_decision)
            
            logger.debug(
                f"Logged bid decision",
                extra={
                    "request_id": bid_request.request_id,
                    "decision": decision,
                    "processing_time_ms": processing_time_ms
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error logging bid decision",
                extra={
                    "request_id": bid_request.request_id,
                    "error": str(e)
                }
            )
            # Don't fail the bid request if logging fails

    async def track_bid_result(
        self,
        request_id: str,
        status: BidRequestStatus,
        win_price: Optional[float] = None
    ) -> None:
        """
        Track bid result (won or lost)
        
        This method is called by the webhook when the ad exchange
        notifies us of the auction result.
        
        Args:
            request_id: Original bid request ID
            status: BID_WON or BID_LOST
            win_price: Actual price paid if won
            
        Requirements: 7.5
        """
        logger.info(
            f"Tracking bid result",
            extra={
                "request_id": request_id,
                "status": status,
                "win_price": win_price
            }
        )
        
        try:
            # Update bid decision status in Firestore
            await self.firestore_service.update_bid_decision_status(
                request_id=request_id,
                status=status,
                win_price=win_price
            )
            
            # Get the bid decision to find campaign
            bid_decision = await self.firestore_service.get_bid_decision(request_id)
            
            if not bid_decision or not bid_decision.campaign_id:
                logger.warning(
                    f"Bid decision not found or missing campaign_id",
                    extra={"request_id": request_id}
                )
                return
            
            # Update bidding strategy
            await self._update_bidding_strategy(
                campaign_id=bid_decision.campaign_id,
                won=status == BidRequestStatus.WON
            )
            
            # If bid was won, update campaign spend
            if status == BidRequestStatus.WON and win_price:
                await self._update_campaign_spend(
                    campaign_id=bid_decision.campaign_id,
                    spend=win_price
                )
            
            logger.info(
                f"Bid result tracked successfully",
                extra={
                    "request_id": request_id,
                    "campaign_id": bid_decision.campaign_id,
                    "status": status
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error tracking bid result",
                extra={
                    "request_id": request_id,
                    "error": str(e)
                }
            )
    
    async def _update_bidding_strategy(
        self,
        campaign_id: str,
        won: bool
    ) -> None:
        """
        Update bidding strategy based on bid result
        
        Adjusts bid prices to maintain target win rate of 20-40%:
        - If win rate too low (<20%): increase bids by 5%
        - If win rate too high (>40%): decrease bids by 5%
        - If within target: no adjustment
        
        Args:
            campaign_id: Campaign identifier
            won: Whether the bid was won
            
        Requirements: 7.5
        """
        try:
            # Get or create bidding strategy
            strategy = await self._get_bidding_strategy(campaign_id)
            
            if not strategy:
                strategy = BiddingStrategy(campaign_id=campaign_id)
            
            # Update bid counts
            strategy.total_bids += 1
            if won:
                strategy.total_wins += 1
            else:
                strategy.total_losses += 1
            
            # Update win rate
            strategy.update_win_rate()
            
            # Check if we should adjust strategy (every 100 bids)
            if strategy.should_adjust_strategy():
                old_factor = strategy.bid_adjustment_factor
                
                if strategy.current_win_rate < self.target_win_rate_min:
                    # Win rate too low - increase bids
                    strategy.bid_adjustment_factor = min(2.0, strategy.bid_adjustment_factor * 1.05)
                    logger.info(
                        f"Increasing bid adjustment factor",
                        extra={
                            "campaign_id": campaign_id,
                            "current_win_rate": strategy.current_win_rate,
                            "target_min": self.target_win_rate_min,
                            "old_factor": old_factor,
                            "new_factor": strategy.bid_adjustment_factor
                        }
                    )
                
                elif strategy.current_win_rate > self.target_win_rate_max:
                    # Win rate too high - decrease bids
                    strategy.bid_adjustment_factor = max(0.5, strategy.bid_adjustment_factor * 0.95)
                    logger.info(
                        f"Decreasing bid adjustment factor",
                        extra={
                            "campaign_id": campaign_id,
                            "current_win_rate": strategy.current_win_rate,
                            "target_max": self.target_win_rate_max,
                            "old_factor": old_factor,
                            "new_factor": strategy.bid_adjustment_factor
                        }
                    )
                
                else:
                    logger.info(
                        f"Win rate within target range",
                        extra={
                            "campaign_id": campaign_id,
                            "current_win_rate": strategy.current_win_rate,
                            "target_range": f"{self.target_win_rate_min}-{self.target_win_rate_max}"
                        }
                    )
            
            # Update timestamp
            strategy.last_updated = datetime.utcnow()
            
            # Save strategy to Firestore
            await self.firestore_service.save_bidding_strategy(strategy)
            
            # Update cache
            self._strategy_cache[campaign_id] = strategy
            
            logger.debug(
                f"Updated bidding strategy",
                extra={
                    "campaign_id": campaign_id,
                    "total_bids": strategy.total_bids,
                    "total_wins": strategy.total_wins,
                    "current_win_rate": strategy.current_win_rate,
                    "bid_adjustment_factor": strategy.bid_adjustment_factor
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error updating bidding strategy",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
    
    async def _get_bidding_strategy(self, campaign_id: str) -> Optional[BiddingStrategy]:
        """
        Get bidding strategy for a campaign
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            BiddingStrategy if found, None otherwise
        """
        try:
            # Check cache first
            if campaign_id in self._strategy_cache:
                return self._strategy_cache[campaign_id]
            
            # Get from Firestore
            strategy = await self.firestore_service.get_bidding_strategy(campaign_id)
            
            if strategy:
                self._strategy_cache[campaign_id] = strategy
            
            return strategy
            
        except Exception as e:
            logger.error(
                f"Error getting bidding strategy",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
            return None
    
    async def _update_campaign_spend(
        self,
        campaign_id: str,
        spend: float
    ) -> None:
        """
        Update campaign spend after winning a bid
        
        Args:
            campaign_id: Campaign identifier
            spend: Amount spent on this bid
        """
        try:
            # Get current allocation
            allocation = await self.firestore_service.get_allocation(campaign_id)
            
            if not allocation:
                logger.warning(
                    f"No allocation found for campaign",
                    extra={"campaign_id": campaign_id}
                )
                return
            
            # Update spend
            allocation.total_spent += spend
            allocation.remaining_budget = allocation.total_budget - allocation.total_spent
            
            # Save updated allocation
            await self.firestore_service.update_allocation(
                campaign_id,
                allocation.model_dump()
            )
            
            logger.debug(
                f"Updated campaign spend",
                extra={
                    "campaign_id": campaign_id,
                    "spend": spend,
                    "total_spent": allocation.total_spent,
                    "remaining_budget": allocation.remaining_budget
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error updating campaign spend",
                extra={
                    "campaign_id": campaign_id,
                    "spend": spend,
                    "error": str(e)
                }
            )
    
    async def get_campaign_bid_stats(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get bid statistics for a campaign
        
        Returns metrics like:
        - Total bids submitted
        - Total wins/losses
        - Win rate
        - Average bid price
        - Average win price
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Dictionary with bid statistics
        """
        try:
            # Get bidding strategy
            strategy = await self._get_bidding_strategy(campaign_id)
            
            if not strategy:
                return {
                    "campaign_id": campaign_id,
                    "total_bids": 0,
                    "total_wins": 0,
                    "total_losses": 0,
                    "win_rate": 0.0,
                    "bid_adjustment_factor": 1.0
                }
            
            # Get bid decisions from Firestore
            bid_decisions = await self.firestore_service.get_bid_decisions_by_campaign(
                campaign_id,
                limit=1000
            )
            
            # Calculate statistics
            total_bid_price = 0.0
            total_win_price = 0.0
            bid_count = 0
            win_count = 0
            
            for decision in bid_decisions:
                if decision.bid_price:
                    total_bid_price += decision.bid_price
                    bid_count += 1
                
                if decision.status == BidRequestStatus.WON:
                    win_count += 1
                    # Win price would be stored separately
            
            avg_bid_price = total_bid_price / bid_count if bid_count > 0 else 0.0
            
            return {
                "campaign_id": campaign_id,
                "total_bids": strategy.total_bids,
                "total_wins": strategy.total_wins,
                "total_losses": strategy.total_losses,
                "win_rate": strategy.current_win_rate,
                "target_win_rate": strategy.target_win_rate,
                "bid_adjustment_factor": strategy.bid_adjustment_factor,
                "avg_bid_price": round(avg_bid_price, 2),
                "last_updated": strategy.last_updated.isoformat()
            }
            
        except Exception as e:
            logger.error(
                f"Error getting campaign bid stats",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
            return {
                "campaign_id": campaign_id,
                "error": str(e)
            }
