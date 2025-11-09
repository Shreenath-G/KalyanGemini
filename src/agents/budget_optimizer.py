"""Budget Optimizer Agent - Allocates budget across platforms and segments"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.models.budget import BudgetAllocation, SegmentAllocation, PlatformSplit
from src.models.audience import AudienceSegment
from src.services.firestore import get_firestore_service
from src.config import settings

logger = logging.getLogger(__name__)


class AgentMessage:
    """Message structure for agent communication"""
    
    def __init__(
        self,
        message_type: str,
        data: Dict[str, Any],
        sender: str = "budget_optimizer",
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


class AgentResponse:
    """Response structure from agent"""
    
    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        agent_name: str = "budget_optimizer"
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.agent_name = agent_name
        self.timestamp = datetime.utcnow()


class BudgetOptimizerAgent:
    """
    Budget Optimizer Agent
    
    Allocates budget across platforms and segments by:
    - Receiving campaign budget and audience segments from Campaign Orchestrator Agent
    - Distributing daily budget with 20% reserved for testing
    - Allocating remaining 80% proportional to segment priority scores
    - Splitting budget across platforms (40% Google, 40% Meta, 20% Programmatic)
    - Calculating maximum cost-per-click bids for each segment
    - Dynamically adjusting budgets based on performance
    - Persisting budget allocations to Firestore
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.2, 9.5, 11.1, 11.2
    """
    
    def __init__(self):
        """Initialize the Budget Optimizer Agent"""
        self.name = "budget_optimizer"
        self.firestore_service = get_firestore_service()
        
        # Default platform split
        self.default_platform_split = PlatformSplit(
            google_ads=0.40,
            meta_ads=0.40,
            programmatic=0.20
        )
        
        logger.info(
            f"Budget Optimizer Agent initialized",
            extra={
                "agent_name": self.name,
                "default_platform_split": {
                    "google_ads": 0.40,
                    "meta_ads": 0.40,
                    "programmatic": 0.20
                }
            }
        )
    
    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        """
        Handle incoming messages from other agents
        
        Supported message types:
        - allocate_budget: Create initial budget allocation for a campaign
        - adjust_budget: Adjust budget based on performance data
        - check_budget: Check budget availability for a segment
        
        Args:
            message: Incoming agent message
            
        Returns:
            Agent response with budget allocation or error
            
        Requirements: 5.1, 11.1, 11.2
        """
        logger.info(
            f"Handling message",
            extra={
                "message_type": message.message_type,
                "correlation_id": message.correlation_id,
                "sender": message.sender
            }
        )
        
        try:
            if message.message_type == "allocate_budget":
                return await self._handle_allocate_budget(message)
            elif message.message_type == "adjust_budget":
                return await self._handle_adjust_budget(message)
            elif message.message_type == "check_budget":
                return await self._handle_check_budget(message)
            else:
                logger.warning(
                    f"Unknown message type: {message.message_type}",
                    extra={"correlation_id": message.correlation_id}
                )
                return AgentResponse(
                    success=False,
                    error=f"Unknown message type: {message.message_type}"
                )
        
        except Exception as e:
            logger.error(
                f"Error handling message",
                extra={
                    "message_type": message.message_type,
                    "correlation_id": message.correlation_id,
                    "error": str(e)
                }
            )
            return AgentResponse(
                success=False,
                error=f"Error processing message: {str(e)}"
            )


# Global agent instance
_agent_instance: Optional[BudgetOptimizerAgent] = None


def get_budget_optimizer_agent() -> BudgetOptimizerAgent:
    """Get or create the global Budget Optimizer Agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = BudgetOptimizerAgent()
    return _agent_instance

    async def _handle_allocate_budget(self, message: AgentMessage) -> AgentResponse:
        """
        Handle allocate_budget message
        
        Args:
            message: Message with campaign data and audience segments
            
        Returns:
            Response with budget allocation plan
        """
        campaign_data = message.data
        campaign_id = campaign_data.get("campaign_id")
        total_budget = campaign_data.get("monthly_budget", 0.0)
        
        logger.info(
            f"Allocating budget for campaign",
            extra={
                "campaign_id": campaign_id,
                "total_budget": total_budget,
                "correlation_id": message.correlation_id
            }
        )
        
        # Get audience segments from context
        segments_data = campaign_data.get("audience_segments", [])
        
        if not segments_data:
            logger.error(
                f"No audience segments provided for budget allocation",
                extra={"campaign_id": campaign_id}
            )
            return AgentResponse(
                success=False,
                error="No audience segments provided for budget allocation"
            )
        
        # Convert segment data to AudienceSegment objects if needed
        segments = []
        for seg_data in segments_data:
            if isinstance(seg_data, dict):
                segments.append(AudienceSegment(**seg_data))
            else:
                segments.append(seg_data)
        
        # Allocate budget across segments
        allocation = self.allocate_budget(
            total_budget=total_budget,
            segments=segments,
            campaign_id=campaign_id
        )
        
        # Calculate bids for each segment
        allocation_with_bids = self.calculate_bids(allocation, segments)
        
        # Persist to Firestore
        await self.persist_allocation(allocation_with_bids)
        
        logger.info(
            f"Budget allocated and persisted",
            extra={
                "campaign_id": campaign_id,
                "total_budget": total_budget,
                "daily_budget": allocation_with_bids.daily_budget,
                "segment_count": len(allocation_with_bids.allocations),
                "correlation_id": message.correlation_id
            }
        )
        
        return AgentResponse(
            success=True,
            data={
                "allocation": allocation_with_bids.model_dump(),
                "segment_count": len(allocation_with_bids.allocations)
            }
        )
    
    def allocate_budget(
        self,
        total_budget: float,
        segments: List[AudienceSegment],
        campaign_id: str
    ) -> BudgetAllocation:
        """
        Allocate budget across audience segments
        
        This method:
        1. Reserves 20% for testing new audiences and creatives
        2. Allocates remaining 80% proportional to segment priority scores
        3. Splits budget across platforms (40% Google, 40% Meta, 20% Programmatic)
        4. Creates SegmentAllocation objects for each segment
        
        Args:
            total_budget: Total monthly budget
            segments: List of audience segments
            campaign_id: Campaign identifier
            
        Returns:
            BudgetAllocation object with segment allocations
            
        Requirements: 5.2, 5.3
        """
        logger.info(
            f"Allocating budget across {len(segments)} segments",
            extra={
                "campaign_id": campaign_id,
                "total_budget": total_budget
            }
        )
        
        # Calculate daily budget
        daily_budget = total_budget / 30
        
        # Reserve 20% for testing
        test_budget = total_budget * 0.20
        main_budget = total_budget * 0.80
        main_daily_budget = main_budget / 30
        
        logger.debug(
            f"Budget breakdown",
            extra={
                "total_budget": total_budget,
                "daily_budget": daily_budget,
                "test_budget": test_budget,
                "main_budget": main_budget,
                "main_daily_budget": main_daily_budget
            }
        )
        
        # Calculate total priority score
        total_priority = sum(seg.priority_score for seg in segments)
        
        if total_priority == 0:
            logger.warning(
                f"Total priority score is 0, using equal distribution",
                extra={"campaign_id": campaign_id}
            )
            total_priority = len(segments)
            for seg in segments:
                seg.priority_score = 1.0
        
        # Allocate main budget proportional to priority scores
        allocations = []
        for segment in segments:
            # Calculate segment's share of main budget
            segment_share = segment.priority_score / total_priority
            segment_daily_budget = main_daily_budget * segment_share
            
            # Create segment allocation with platform split
            segment_allocation = SegmentAllocation(
                segment_id=segment.segment_id,
                daily_budget=segment_daily_budget,
                platform_split=self.default_platform_split,
                max_cpc=0.0,  # Will be calculated in calculate_bids
                current_spend=0.0
            )
            
            allocations.append(segment_allocation)
            
            logger.debug(
                f"Allocated budget to segment",
                extra={
                    "segment_id": segment.segment_id,
                    "segment_name": segment.name,
                    "priority_score": segment.priority_score,
                    "segment_share": segment_share,
                    "daily_budget": segment_daily_budget
                }
            )
        
        # Create budget allocation object
        budget_allocation = BudgetAllocation(
            campaign_id=campaign_id,
            total_budget=total_budget,
            daily_budget=daily_budget,
            test_budget=test_budget,
            allocations=allocations,
            total_spent=0.0,
            remaining_budget=total_budget
        )
        
        logger.info(
            f"Budget allocation complete",
            extra={
                "campaign_id": campaign_id,
                "segment_count": len(allocations),
                "total_daily_allocation": budget_allocation.get_total_daily_allocation()
            }
        )
        
        return budget_allocation

    def calculate_bids(
        self,
        allocation: BudgetAllocation,
        segments: List[AudienceSegment]
    ) -> BudgetAllocation:
        """
        Calculate maximum CPC bids for each segment
        
        This method:
        1. Determines max CPC for each segment based on estimated conversion value
        2. Adjusts bids based on competition and segment characteristics
        3. Ensures total allocated spend stays within budget (+/- 5%)
        4. Returns BudgetAllocation with calculated bids
        
        Bid calculation formula:
        - Base CPC = (estimated conversion value * conversion probability) / target ROAS
        - Adjusted for segment size and competition
        - Typical range: $0.50 - $10.00
        
        Args:
            allocation: BudgetAllocation object with segment allocations
            segments: List of audience segments with conversion probabilities
            
        Returns:
            BudgetAllocation with calculated max_cpc values
            
        Requirements: 5.3, 5.4, 5.5
        """
        logger.info(
            f"Calculating bids for {len(allocation.allocations)} segment allocations",
            extra={"campaign_id": allocation.campaign_id}
        )
        
        # Create segment lookup map
        segment_map = {seg.segment_id: seg for seg in segments}
        
        # Calculate bids for each allocation
        for alloc in allocation.allocations:
            segment = segment_map.get(alloc.segment_id)
            
            if not segment:
                logger.warning(
                    f"Segment not found for allocation, using default bid",
                    extra={"segment_id": alloc.segment_id}
                )
                alloc.max_cpc = 2.00  # Default bid
                continue
            
            # Calculate max CPC based on segment characteristics
            max_cpc = self._calculate_max_cpc(
                segment=segment,
                daily_budget=alloc.daily_budget
            )
            
            alloc.max_cpc = max_cpc
            
            logger.debug(
                f"Calculated bid for segment",
                extra={
                    "segment_id": segment.segment_id,
                    "segment_name": segment.name,
                    "conversion_probability": segment.conversion_probability,
                    "priority_score": segment.priority_score,
                    "max_cpc": max_cpc,
                    "daily_budget": alloc.daily_budget
                }
            )
        
        # Validate total allocation stays within budget (+/- 5%)
        self._validate_budget_constraints(allocation)
        
        logger.info(
            f"Bid calculation complete",
            extra={
                "campaign_id": allocation.campaign_id,
                "avg_max_cpc": sum(a.max_cpc for a in allocation.allocations) / len(allocation.allocations),
                "min_max_cpc": min(a.max_cpc for a in allocation.allocations),
                "max_max_cpc": max(a.max_cpc for a in allocation.allocations)
            }
        )
        
        return allocation
    
    def _calculate_max_cpc(
        self,
        segment: AudienceSegment,
        daily_budget: float
    ) -> float:
        """
        Calculate maximum CPC for a segment
        
        Formula:
        - Estimated conversion value: $50 (average for SMB products)
        - Target ROAS: 3.0 (industry standard)
        - Base CPC = (conversion_value * conversion_probability) / target_ROAS
        - Adjusted for segment size and competition
        
        Args:
            segment: Audience segment with conversion probability
            daily_budget: Daily budget for this segment
            
        Returns:
            Maximum CPC bid amount
        """
        # Estimated conversion value (average order value for SMB products)
        estimated_conversion_value = 50.0
        
        # Target ROAS (return on ad spend)
        target_roas = 3.0
        
        # Base CPC calculation
        # CPC = (conversion_value * conversion_probability) / target_ROAS
        base_cpc = (estimated_conversion_value * segment.conversion_probability) / target_roas
        
        # Adjust for segment size (larger segments = more competition = higher bids)
        from src.models.audience import SegmentSize
        
        if segment.estimated_size == SegmentSize.LARGE:
            size_multiplier = 1.3  # More competition in large segments
        elif segment.estimated_size == SegmentSize.SMALL:
            size_multiplier = 0.8  # Less competition in small segments
        else:  # MEDIUM
            size_multiplier = 1.0
        
        adjusted_cpc = base_cpc * size_multiplier
        
        # Ensure CPC is within reasonable bounds
        # Min: $0.50, Max: $10.00
        max_cpc = max(0.50, min(10.00, adjusted_cpc))
        
        # Ensure we can get at least 10 clicks per day with this budget
        # If daily_budget / max_cpc < 10, reduce max_cpc
        min_clicks_per_day = 10
        if daily_budget / max_cpc < min_clicks_per_day:
            max_cpc = daily_budget / min_clicks_per_day
            max_cpc = max(0.50, max_cpc)  # Still enforce minimum
        
        return round(max_cpc, 2)
    
    def _validate_budget_constraints(self, allocation: BudgetAllocation) -> None:
        """
        Validate that budget allocation stays within constraints
        
        Checks:
        - Total allocated spend doesn't exceed budget by more than 5%
        - All allocations have positive budgets
        - Platform splits are valid
        
        Args:
            allocation: BudgetAllocation to validate
            
        Raises:
            ValueError: If budget constraints are violated
        """
        # Calculate total monthly allocation
        total_daily_allocation = allocation.get_total_daily_allocation()
        total_monthly_allocation = total_daily_allocation * 30
        
        # Main budget (excluding test budget)
        main_budget = allocation.total_budget - allocation.test_budget
        
        # Check if allocation exceeds budget by more than 5%
        if total_monthly_allocation > main_budget * 1.05:
            logger.error(
                f"Budget allocation exceeds limit",
                extra={
                    "campaign_id": allocation.campaign_id,
                    "total_monthly_allocation": total_monthly_allocation,
                    "main_budget": main_budget,
                    "excess_percent": ((total_monthly_allocation / main_budget) - 1) * 100
                }
            )
            raise ValueError(
                f"Total allocated spend ({total_monthly_allocation}) exceeds "
                f"main budget ({main_budget}) by more than 5%"
            )
        
        # Check all allocations have positive budgets
        for alloc in allocation.allocations:
            if alloc.daily_budget <= 0:
                raise ValueError(
                    f"Segment {alloc.segment_id} has non-positive daily budget: {alloc.daily_budget}"
                )
            if alloc.max_cpc <= 0:
                raise ValueError(
                    f"Segment {alloc.segment_id} has non-positive max CPC: {alloc.max_cpc}"
                )
        
        logger.debug(
            f"Budget constraints validated",
            extra={
                "campaign_id": allocation.campaign_id,
                "total_monthly_allocation": total_monthly_allocation,
                "main_budget": main_budget,
                "utilization_percent": (total_monthly_allocation / main_budget) * 100
            }
        )

    async def _handle_adjust_budget(self, message: AgentMessage) -> AgentResponse:
        """
        Handle adjust_budget message for performance-based reallocation
        
        Args:
            message: Message with campaign performance data
            
        Returns:
            Response with adjusted budget allocation
        """
        campaign_data = message.data
        campaign_id = campaign_data.get("campaign_id")
        performance_data = campaign_data.get("performance_data", {})
        optimization_mode = campaign_data.get("optimization_mode", "standard")
        
        logger.info(
            f"Adjusting budget for campaign",
            extra={
                "campaign_id": campaign_id,
                "optimization_mode": optimization_mode,
                "correlation_id": message.correlation_id
            }
        )
        
        # Get current allocation from Firestore
        current_allocation = await self.firestore_service.get_allocation(campaign_id)
        
        if not current_allocation:
            logger.error(
                f"No existing allocation found for campaign",
                extra={"campaign_id": campaign_id}
            )
            return AgentResponse(
                success=False,
                error=f"No existing allocation found for campaign {campaign_id}"
            )
        
        # Adjust budget based on performance
        adjusted_allocation = self.adjust_budget(
            allocation=current_allocation,
            performance_data=performance_data,
            optimization_mode=optimization_mode
        )
        
        # Persist updated allocation
        await self.firestore_service.update_allocation(
            campaign_id,
            adjusted_allocation.model_dump()
        )
        
        logger.info(
            f"Budget adjusted and persisted",
            extra={
                "campaign_id": campaign_id,
                "adjustments_made": len(adjusted_allocation.allocations),
                "correlation_id": message.correlation_id
            }
        )
        
        return AgentResponse(
            success=True,
            data={
                "allocation": adjusted_allocation.model_dump(),
                "adjustments_made": True
            }
        )
    
    def adjust_budget(
        self,
        allocation: BudgetAllocation,
        performance_data: Dict[str, Any],
        optimization_mode: str = "standard"
    ) -> BudgetAllocation:
        """
        Adjust budget allocation based on performance data
        
        This method:
        1. Increases budgets for high-performing segments (ROAS > 4.0)
        2. Decreases budgets for underperforming segments (ROAS < 1.0)
        3. Respects budget constraints and optimization mode settings
        4. Returns updated BudgetAllocation
        
        Adjustment rules:
        - High performers (ROAS > 4.0): Increase budget by 50%
        - Underperformers (ROAS < 1.0): Decrease budget by 30%
        - Aggressive mode: More aggressive adjustments (70% increase, 50% decrease)
        - Ensure total allocation stays within budget
        
        Args:
            allocation: Current budget allocation
            performance_data: Performance metrics by segment
            optimization_mode: "standard" or "aggressive"
            
        Returns:
            Adjusted BudgetAllocation
            
        Requirements: 9.2, 9.5
        """
        logger.info(
            f"Adjusting budget based on performance",
            extra={
                "campaign_id": allocation.campaign_id,
                "optimization_mode": optimization_mode,
                "segment_count": len(allocation.allocations)
            }
        )
        
        # Determine adjustment factors based on optimization mode
        if optimization_mode == "aggressive":
            high_performer_increase = 0.70  # 70% increase
            underperformer_decrease = 0.50  # 50% decrease
        else:  # standard
            high_performer_increase = 0.50  # 50% increase
            underperformer_decrease = 0.30  # 30% decrease
        
        # Track adjustments
        adjustments = []
        
        # Calculate adjustments for each segment
        for alloc in allocation.allocations:
            segment_id = alloc.segment_id
            segment_performance = performance_data.get(segment_id, {})
            
            roas = segment_performance.get("roas", 0.0)
            clicks = segment_performance.get("clicks", 0)
            
            original_budget = alloc.daily_budget
            adjustment_factor = 1.0
            adjustment_reason = "no_change"
            
            # Only adjust if we have enough data (at least 50 clicks)
            if clicks >= 50:
                if roas > 4.0:
                    # High performer - increase budget
                    adjustment_factor = 1.0 + high_performer_increase
                    adjustment_reason = "high_roas"
                    logger.info(
                        f"Increasing budget for high performer",
                        extra={
                            "segment_id": segment_id,
                            "roas": roas,
                            "clicks": clicks,
                            "adjustment_factor": adjustment_factor
                        }
                    )
                elif roas < 1.0:
                    # Underperformer - decrease budget
                    adjustment_factor = 1.0 - underperformer_decrease
                    adjustment_reason = "low_roas"
                    logger.info(
                        f"Decreasing budget for underperformer",
                        extra={
                            "segment_id": segment_id,
                            "roas": roas,
                            "clicks": clicks,
                            "adjustment_factor": adjustment_factor
                        }
                    )
            
            # Apply adjustment
            new_budget = original_budget * adjustment_factor
            
            # Ensure minimum budget of $5/day
            new_budget = max(5.0, new_budget)
            
            alloc.daily_budget = round(new_budget, 2)
            
            if adjustment_factor != 1.0:
                adjustments.append({
                    "segment_id": segment_id,
                    "original_budget": original_budget,
                    "new_budget": new_budget,
                    "adjustment_factor": adjustment_factor,
                    "reason": adjustment_reason,
                    "roas": roas
                })
        
        # Normalize allocations to stay within budget constraints
        self._normalize_allocations(allocation)
        
        # Update timestamp
        allocation.last_updated = datetime.utcnow()
        
        logger.info(
            f"Budget adjustment complete",
            extra={
                "campaign_id": allocation.campaign_id,
                "adjustments_count": len(adjustments),
                "total_daily_allocation": allocation.get_total_daily_allocation()
            }
        )
        
        if adjustments:
            logger.debug(
                f"Budget adjustments made",
                extra={"adjustments": adjustments}
            )
        
        return allocation
    
    def _normalize_allocations(self, allocation: BudgetAllocation) -> None:
        """
        Normalize segment allocations to stay within budget constraints
        
        If total allocation exceeds main budget, proportionally reduce all allocations
        to fit within budget (+/- 5% tolerance)
        
        Args:
            allocation: BudgetAllocation to normalize (modified in place)
        """
        # Calculate current total
        total_daily = allocation.get_total_daily_allocation()
        total_monthly = total_daily * 30
        
        # Main budget (excluding test budget)
        main_budget = allocation.total_budget - allocation.test_budget
        
        # Check if we exceed budget by more than 5%
        if total_monthly > main_budget * 1.05:
            # Calculate normalization factor
            normalization_factor = (main_budget * 1.05) / total_monthly
            
            logger.warning(
                f"Total allocation exceeds budget, normalizing",
                extra={
                    "campaign_id": allocation.campaign_id,
                    "total_monthly": total_monthly,
                    "main_budget": main_budget,
                    "normalization_factor": normalization_factor
                }
            )
            
            # Apply normalization to all allocations
            for alloc in allocation.allocations:
                alloc.daily_budget = round(alloc.daily_budget * normalization_factor, 2)
                # Ensure minimum budget
                alloc.daily_budget = max(5.0, alloc.daily_budget)
            
            logger.info(
                f"Allocations normalized",
                extra={
                    "campaign_id": allocation.campaign_id,
                    "new_total_daily": allocation.get_total_daily_allocation()
                }
            )
    
    async def _handle_check_budget(self, message: AgentMessage) -> AgentResponse:
        """
        Handle check_budget message to verify budget availability
        
        Args:
            message: Message with campaign_id and segment_id
            
        Returns:
            Response with budget availability information
        """
        campaign_id = message.data.get("campaign_id")
        segment_id = message.data.get("segment_id")
        
        logger.debug(
            f"Checking budget availability",
            extra={
                "campaign_id": campaign_id,
                "segment_id": segment_id,
                "correlation_id": message.correlation_id
            }
        )
        
        # Get current allocation
        allocation = await self.firestore_service.get_allocation(campaign_id)
        
        if not allocation:
            return AgentResponse(
                success=False,
                error=f"No allocation found for campaign {campaign_id}"
            )
        
        # Find segment allocation
        try:
            segment_alloc = allocation.get_allocation_by_segment(segment_id)
            remaining = segment_alloc.get_remaining_budget()
            
            return AgentResponse(
                success=True,
                data={
                    "available": remaining > 0,
                    "remaining": remaining,
                    "daily_budget": segment_alloc.daily_budget,
                    "current_spend": segment_alloc.current_spend
                }
            )
        except ValueError as e:
            return AgentResponse(
                success=False,
                error=str(e)
            )

    async def persist_allocation(self, allocation: BudgetAllocation) -> str:
        """
        Persist budget allocation to Firestore
        
        This method:
        1. Saves budget allocation using FirestoreService.create_allocation
        2. Updates campaign with budget_allocation reference
        
        Args:
            allocation: BudgetAllocation object to persist
            
        Returns:
            Campaign ID of the persisted allocation
            
        Requirements: 5.1, 13.1
        """
        campaign_id = allocation.campaign_id
        
        logger.info(
            f"Persisting budget allocation to Firestore",
            extra={
                "campaign_id": campaign_id,
                "total_budget": allocation.total_budget,
                "segment_count": len(allocation.allocations)
            }
        )
        
        try:
            # Save allocation to Firestore
            await self.firestore_service.create_allocation(allocation)
            
            # Update campaign with budget_allocation reference
            campaign = await self.firestore_service.get_campaign(campaign_id)
            
            if campaign:
                # Update campaign with budget allocation data
                await self.firestore_service.update_campaign(
                    campaign_id,
                    {
                        "budget_allocation": allocation.model_dump(),
                        "last_updated": datetime.utcnow()
                    }
                )
                
                logger.info(
                    f"Successfully persisted allocation and updated campaign",
                    extra={
                        "campaign_id": campaign_id,
                        "total_budget": allocation.total_budget,
                        "daily_budget": allocation.daily_budget,
                        "segment_count": len(allocation.allocations)
                    }
                )
            else:
                logger.warning(
                    f"Campaign not found, allocation persisted but campaign not updated",
                    extra={"campaign_id": campaign_id}
                )
            
            return campaign_id
            
        except Exception as e:
            logger.error(
                f"Error persisting allocation to Firestore",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
            raise
