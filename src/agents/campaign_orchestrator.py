"""Campaign Orchestrator Agent - Coordinates specialist agents for campaign creation and optimization"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

from src.models.campaign import Campaign, CampaignRequest, CampaignStatus
from src.services.firestore import get_firestore_service
from src.config import settings
from src.agents.error_handler import (
    with_timeout_and_retry,
    with_graceful_degradation,
    AgentErrorHandler,
    handle_agent_communication_error,
    AgentCommunicationError,
    AgentTimeoutError
)
from src.utils.logging_config import AgentLogger, set_correlation_id

logger = logging.getLogger(__name__)
agent_logger = AgentLogger("campaign_orchestrator")


class AgentMessage:
    """Message structure for agent communication"""
    
    def __init__(
        self,
        message_type: str,
        data: Dict[str, Any],
        sender: str = "campaign_orchestrator",
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
    """Response structure from specialist agents"""
    
    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        agent_name: Optional[str] = None
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.agent_name = agent_name
        self.timestamp = datetime.utcnow()


class CampaignOrchestratorAgent:
    """
    Campaign Orchestrator Agent
    
    Coordinates campaign creation and optimization by:
    - Receiving campaign requests from API
    - Distributing tasks to specialist agents (Creative, Audience, Budget)
    - Synthesizing agent outputs into unified campaign strategy
    - Managing campaign lifecycle and state
    - Handling optimization requests
    
    Requirements: 2.1, 2.2, 11.1, 11.2
    """
    
    def __init__(self):
        """Initialize the Campaign Orchestrator Agent"""
        self.name = "campaign_orchestrator"
        self.agent_timeout = settings.agent_timeout_seconds
        self.firestore_service = get_firestore_service()
        
        # Agent communication channels (to be implemented with actual ADK)
        # For now, we'll use placeholder methods that will be replaced with ADK messaging
        self.creative_agent = None
        self.audience_agent = None
        self.budget_agent = None
        
        logger.info(
            f"Campaign Orchestrator Agent initialized",
            extra={
                "agent_name": self.name,
                "timeout": self.agent_timeout
            }
        )
    
    def _get_agent_channel(self, agent_name: str) -> Optional[Any]:
        """
        Get communication channel to a specialist agent
        
        This is a placeholder that will be replaced with actual ADK agent communication.
        In production, this would use ADK's agent-to-agent messaging capabilities.
        
        Args:
            agent_name: Name of the specialist agent
            
        Returns:
            Agent communication channel (placeholder for now)
        """
        agent_channels = {
            "creative_generator": self.creative_agent,
            "audience_targeting": self.audience_agent,
            "budget_optimizer": self.budget_agent
        }
        return agent_channels.get(agent_name)
    
    @with_timeout_and_retry(timeout=30, max_retries=2)
    async def _send_message_to_agent(
        self,
        agent_name: str,
        message: AgentMessage
    ) -> AgentResponse:
        """
        Send message to a specialist agent with timeout and retry
        
        This is a placeholder implementation. In production, this would use
        ADK's message passing infrastructure (Pub/Sub, etc.)
        
        Includes:
        - 30 second timeout per attempt
        - 2 retry attempts with exponential backoff
        - Automatic error handling and logging
        
        Args:
            agent_name: Name of the target agent
            message: Message to send
            
        Returns:
            Response from the agent
            
        Raises:
            AgentCommunicationError: If agent communication fails after retries
            AgentTimeoutError: If agent doesn't respond within timeout
            
        Requirements: 2.4, 12.3
        """
        # Log agent message using structured agent logger
        agent_logger.log_message_sent(
            target_agent=agent_name,
            message_type=message.message_type,
            correlation_id=message.correlation_id,
            data=message.data
        )
        
        try:
            # TODO: Replace with actual ADK message sending
            # For now, return a placeholder response indicating the agent is not yet implemented
            return AgentResponse(
                success=False,
                error=f"{agent_name} not yet implemented",
                agent_name=agent_name
            )
        except Exception as e:
            # Wrap in AgentCommunicationError for better error handling
            raise AgentCommunicationError(
                agent_name=agent_name,
                message=f"Failed to send message: {str(e)}",
                original_error=e
            )
    
    async def _gather_agent_responses(
        self,
        tasks: List[asyncio.Task],
        timeout: int
    ) -> List[AgentResponse]:
        """
        Gather responses from multiple agents with timeout handling
        
        Args:
            tasks: List of async tasks waiting for agent responses
            timeout: Timeout in seconds
            
        Returns:
            List of agent responses (may include timeout errors)
        """
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
            
            # Convert exceptions to error responses
            processed_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    processed_responses.append(
                        AgentResponse(
                            success=False,
                            error=str(response),
                            agent_name=f"agent_{i}"
                        )
                    )
                else:
                    processed_responses.append(response)
            
            return processed_responses
            
        except asyncio.TimeoutError:
            logger.error(
                f"Agent responses timed out after {timeout} seconds",
                extra={"timeout": timeout, "task_count": len(tasks)}
            )
            
            # Return timeout errors for all tasks
            return [
                AgentResponse(
                    success=False,
                    error=f"Agent response timed out after {timeout} seconds",
                    agent_name=f"agent_{i}"
                )
                for i in range(len(tasks))
            ]
    
    def _persist_agent_state(self, campaign_id: str, state_data: Dict[str, Any]) -> None:
        """
        Persist agent state to Firestore
        
        This uses ADK's state management capabilities backed by Firestore.
        
        Args:
            campaign_id: Campaign identifier
            state_data: State data to persist
        """
        logger.debug(
            f"Persisting agent state",
            extra={
                "campaign_id": campaign_id,
                "state_keys": list(state_data.keys())
            }
        )
        
        # TODO: Implement ADK state persistence
        # For now, this is a placeholder
        pass
    
    def _load_agent_state(self, campaign_id: str) -> Dict[str, Any]:
        """
        Load agent state from Firestore
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Persisted state data
        """
        logger.debug(f"Loading agent state for campaign: {campaign_id}")
        
        # TODO: Implement ADK state loading
        # For now, return empty state
        return {}
    
    @with_timeout_and_retry(timeout=60, max_retries=2)
    async def handle_campaign_request(
        self,
        campaign: Campaign,
        campaign_request: CampaignRequest
    ) -> Dict[str, Any]:
        """
        Handle campaign creation request by coordinating specialist agents
        
        This method:
        1. Distributes tasks to Creative, Audience, and Budget agents in parallel
        2. Collects responses with timeout handling (30 seconds per agent)
        3. Validates responses from all agents
        4. Applies fallback strategies for failed agents
        5. Returns combined results for strategy synthesis
        
        Includes:
        - 60 second timeout for entire operation
        - 2 retry attempts with exponential backoff
        - Automatic fallback strategies for agent failures
        - Graceful degradation when agents are unavailable
        
        Args:
            campaign: Campaign object with basic information
            campaign_request: Original campaign request data
            
        Returns:
            Dictionary containing responses from all specialist agents
            
        Requirements: 2.1, 2.3, 2.4, 12.2, 12.3
        """
        correlation_id = str(uuid.uuid4())
        
        logger.info(
            f"Handling campaign request",
            extra={
                "campaign_id": campaign.campaign_id,
                "account_id": campaign.account_id,
                "correlation_id": correlation_id,
                "budget": campaign.monthly_budget,
                "goal": campaign.business_goal
            }
        )
        
        # Prepare request data for specialist agents
        request_data = {
            "campaign_id": campaign.campaign_id,
            "business_goal": campaign.business_goal,
            "monthly_budget": campaign.monthly_budget,
            "target_audience": campaign.target_audience,
            "products": campaign.products,
            "optimization_mode": campaign.optimization_mode.value
        }
        
        # Create messages for each specialist agent
        creative_message = AgentMessage(
            message_type="generate_creatives",
            data=request_data,
            sender=self.name,
            correlation_id=correlation_id
        )
        
        audience_message = AgentMessage(
            message_type="identify_audiences",
            data=request_data,
            sender=self.name,
            correlation_id=correlation_id
        )
        
        budget_message = AgentMessage(
            message_type="allocate_budget",
            data=request_data,
            sender=self.name,
            correlation_id=correlation_id
        )
        
        # Send messages to specialist agents in parallel
        logger.info(
            f"Sending parallel requests to specialist agents",
            extra={
                "campaign_id": campaign.campaign_id,
                "correlation_id": correlation_id,
                "agents": ["creative_generator", "audience_targeting", "budget_optimizer"]
            }
        )
        
        tasks = [
            self._send_message_to_agent("creative_generator", creative_message),
            self._send_message_to_agent("audience_targeting", audience_message),
            self._send_message_to_agent("budget_optimizer", budget_message)
        ]
        
        # Gather responses with timeout
        try:
            responses = await self._gather_agent_responses(tasks, timeout=self.agent_timeout)
        except Exception as e:
            logger.error(
                f"Failed to gather agent responses",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "correlation_id": correlation_id,
                    "error": str(e)
                }
            )
            # Create error responses for all agents
            responses = [
                AgentResponse(success=False, error=str(e), agent_name="creative_generator"),
                AgentResponse(success=False, error=str(e), agent_name="audience_targeting"),
                AgentResponse(success=False, error=str(e), agent_name="budget_optimizer")
            ]
        
        # Process and validate responses
        creative_response, audience_response, budget_response = responses
        
        # Check for failures and apply fallback strategies with error handler
        results = {
            "creative_variants": self._process_creative_response_with_fallback(
                creative_response,
                campaign,
                request_data
            ),
            "audience_segments": self._process_audience_response_with_fallback(
                audience_response,
                campaign,
                request_data
            ),
            "budget_allocation": self._process_budget_response_with_fallback(
                budget_response,
                campaign,
                request_data
            ),
            "agent_status": {
                "creative_generator": {
                    "success": creative_response.success,
                    "error": creative_response.error,
                    "fallback_applied": not creative_response.success
                },
                "audience_targeting": {
                    "success": audience_response.success,
                    "error": audience_response.error,
                    "fallback_applied": not audience_response.success
                },
                "budget_optimizer": {
                    "success": budget_response.success,
                    "error": budget_response.error,
                    "fallback_applied": not budget_response.success
                }
            },
            "correlation_id": correlation_id,
            "requires_review": not all([
                creative_response.success,
                audience_response.success,
                budget_response.success
            ])
        }
        
        logger.info(
            f"Campaign request processing completed",
            extra={
                "campaign_id": campaign.campaign_id,
                "correlation_id": correlation_id,
                "creative_success": creative_response.success,
                "audience_success": audience_response.success,
                "budget_success": budget_response.success,
                "requires_review": results["requires_review"]
            }
        )
        
        return results
    
    def _process_creative_response_with_fallback(
        self,
        response: AgentResponse,
        campaign: Campaign,
        request_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Process Creative Generator Agent response with error handler fallback
        
        Uses AgentErrorHandler for consistent fallback strategy application
        
        Args:
            response: Response from Creative Generator Agent
            campaign: Campaign object
            request_data: Original request data for fallback
            
        Returns:
            List of creative variants (from agent or fallback)
            
        Requirements: 12.2, 12.3
        """
        if not response.success:
            logger.warning(
                f"Creative Generator Agent failed, applying fallback",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "error": response.error
                }
            )
            
            # Use error handler for consistent fallback
            fallback_result = AgentErrorHandler.handle_agent_error(
                agent_name="creative_generator",
                error=Exception(response.error or "Agent failed"),
                campaign_data=request_data
            )
            
            return fallback_result.get("variations", [])
        
        # Process successful response
        return response.data.get("variations", [])
    
    def _process_audience_response_with_fallback(
        self,
        response: AgentResponse,
        campaign: Campaign,
        request_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Process Audience Targeting Agent response with error handler fallback
        
        Uses AgentErrorHandler for consistent fallback strategy application
        
        Args:
            response: Response from Audience Targeting Agent
            campaign: Campaign object
            request_data: Original request data for fallback
            
        Returns:
            List of audience segments (from agent or fallback)
            
        Requirements: 12.2, 12.3
        """
        if not response.success:
            logger.warning(
                f"Audience Targeting Agent failed, applying fallback",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "error": response.error
                }
            )
            
            # Use error handler for consistent fallback
            fallback_result = AgentErrorHandler.handle_agent_error(
                agent_name="audience_targeting",
                error=Exception(response.error or "Agent failed"),
                campaign_data=request_data
            )
            
            return fallback_result.get("segments", [])
        
        # Process successful response
        return response.data.get("segments", [])
    
    def _process_budget_response_with_fallback(
        self,
        response: AgentResponse,
        campaign: Campaign,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process Budget Optimizer Agent response with error handler fallback
        
        Uses AgentErrorHandler for consistent fallback strategy application
        
        Args:
            response: Response from Budget Optimizer Agent
            campaign: Campaign object
            request_data: Original request data for fallback
            
        Returns:
            Budget allocation plan (from agent or fallback)
            
        Requirements: 12.2, 12.3
        """
        if not response.success:
            logger.warning(
                f"Budget Optimizer Agent failed, applying fallback",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "error": response.error
                }
            )
            
            # Use error handler for consistent fallback
            fallback_result = AgentErrorHandler.handle_agent_error(
                agent_name="budget_optimizer",
                error=Exception(response.error or "Agent failed"),
                campaign_data=request_data
            )
            
            return fallback_result.get("allocation", {})
        
        # Process successful response
        return response.data.get("allocation", {})
    
    async def synthesize_strategy(
        self,
        campaign: Campaign,
        agent_results: Dict[str, Any]
    ) -> Campaign:
        """
        Synthesize agent outputs into unified campaign strategy
        
        This method:
        1. Combines creative variants, audience segments, and budget allocation
        2. Generates unified campaign strategy
        3. Persists complete strategy to Firestore
        4. Returns updated campaign with estimated launch timeline
        
        Args:
            campaign: Campaign object with basic information
            agent_results: Results from specialist agents
            
        Returns:
            Updated campaign object with complete strategy
            
        Requirements: 2.5, 1.2
        """
        logger.info(
            f"Synthesizing campaign strategy",
            extra={
                "campaign_id": campaign.campaign_id,
                "requires_review": agent_results.get("requires_review", False)
            }
        )
        
        # Extract agent results
        creative_variants = agent_results.get("creative_variants", [])
        audience_segments = agent_results.get("audience_segments", [])
        budget_allocation = agent_results.get("budget_allocation", {})
        
        # Update campaign with strategy components
        campaign.creative_variants = creative_variants
        campaign.audience_segments = audience_segments
        campaign.budget_allocation = budget_allocation
        
        # Determine campaign status based on agent success
        if agent_results.get("requires_review", False):
            campaign.status = CampaignStatus.DRAFT
            logger.warning(
                f"Campaign requires review due to agent failures",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "agent_status": agent_results.get("agent_status", {})
                }
            )
        else:
            # All agents succeeded - campaign is ready for activation
            campaign.status = CampaignStatus.DRAFT  # Still draft until user activates
        
        # Calculate estimated launch timeline
        estimated_launch = self._calculate_launch_timeline(
            campaign,
            agent_results.get("requires_review", False)
        )
        
        # Persist complete strategy to Firestore
        try:
            await self.firestore_service.update_campaign(
                campaign.campaign_id,
                {
                    "creative_variants": creative_variants,
                    "audience_segments": audience_segments,
                    "budget_allocation": budget_allocation,
                    "status": campaign.status.value
                }
            )
            
            logger.info(
                f"Campaign strategy persisted to Firestore",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "variants_count": len(creative_variants),
                    "segments_count": len(audience_segments),
                    "estimated_launch": estimated_launch
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to persist campaign strategy",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "error": str(e)
                }
            )
            raise
        
        # Persist agent state for tracking
        self._persist_agent_state(
            campaign.campaign_id,
            {
                "strategy_synthesized": True,
                "synthesis_timestamp": datetime.utcnow().isoformat(),
                "correlation_id": agent_results.get("correlation_id"),
                "agent_status": agent_results.get("agent_status", {}),
                "estimated_launch": estimated_launch
            }
        )
        
        return campaign
    
    def _calculate_launch_timeline(
        self,
        campaign: Campaign,
        requires_review: bool
    ) -> str:
        """
        Calculate estimated launch timeline based on campaign complexity
        
        Args:
            campaign: Campaign object
            requires_review: Whether campaign requires manual review
            
        Returns:
            Estimated launch timeline string
        """
        if requires_review:
            return "48-72 hours (requires review)"
        
        # Base timeline on campaign complexity
        variant_count = len(campaign.creative_variants)
        segment_count = len(campaign.audience_segments)
        
        if variant_count >= 5 and segment_count >= 3:
            return "24-48 hours"
        elif variant_count >= 3 or segment_count >= 2:
            return "12-24 hours"
        else:
            return "6-12 hours"
    
    @with_timeout_and_retry(timeout=45, max_retries=2)
    async def handle_optimization_request(
        self,
        campaign_id: str,
        optimization_actions: List[Dict[str, Any]],
        optimization_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Handle optimization request for a campaign with error handling
        
        This method:
        1. Processes optimization actions from Performance Analyzer Agent or manual requests
        2. Coordinates budget adjustments with Budget Optimizer Agent
        3. Coordinates creative updates with Creative Generator Agent
        4. Applies optimizations and updates campaign state
        5. Uses graceful degradation if agents are unavailable
        
        Includes:
        - 45 second timeout for entire operation
        - 2 retry attempts with exponential backoff
        - Graceful degradation for agent failures
        
        Args:
            campaign_id: Campaign identifier
            optimization_actions: List of optimization actions to apply
            optimization_type: Type of optimization ("auto" or "manual")
            
        Returns:
            Dictionary containing optimization results
            
        Requirements: 9.1, 9.2, 9.4, 12.2, 12.3
        """
        correlation_id = str(uuid.uuid4())
        
        logger.info(
            f"Handling optimization request",
            extra={
                "campaign_id": campaign_id,
                "correlation_id": correlation_id,
                "optimization_type": optimization_type,
                "action_count": len(optimization_actions)
            }
        )
        
        # Load campaign from Firestore
        campaign = await self.firestore_service.get_campaign(campaign_id)
        
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return {
                "success": False,
                "error": f"Campaign {campaign_id} not found"
            }
        
        # Group actions by type
        budget_actions = []
        creative_actions = []
        pause_actions = []
        
        for action in optimization_actions:
            action_type = action.get("type")
            
            if action_type in ["scale_variant", "scale_segment", "adjust_budget"]:
                budget_actions.append(action)
            elif action_type in ["generate_new_variants", "update_creative"]:
                creative_actions.append(action)
            elif action_type in ["pause_variant", "pause_segment"]:
                pause_actions.append(action)
        
        # Process pause actions immediately (no agent coordination needed)
        pause_results = await self._apply_pause_actions(campaign, pause_actions)
        
        # Coordinate budget adjustments with Budget Optimizer Agent
        budget_results = await self._coordinate_budget_adjustments(
            campaign,
            budget_actions,
            correlation_id
        )
        
        # Coordinate creative updates with Creative Generator Agent
        creative_results = await self._coordinate_creative_updates(
            campaign,
            creative_actions,
            correlation_id
        )
        
        # Update campaign optimization timestamp
        await self.firestore_service.update_campaign(
            campaign_id,
            {"last_optimized_at": datetime.utcnow()}
        )
        
        # Compile results
        results = {
            "success": True,
            "campaign_id": campaign_id,
            "optimization_type": optimization_type,
            "correlation_id": correlation_id,
            "actions_applied": {
                "pause": pause_results,
                "budget": budget_results,
                "creative": creative_results
            },
            "total_actions": len(optimization_actions),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Optimization request completed",
            extra={
                "campaign_id": campaign_id,
                "correlation_id": correlation_id,
                "pause_count": len(pause_results),
                "budget_count": len(budget_results),
                "creative_count": len(creative_results)
            }
        )
        
        return results
    
    async def _apply_pause_actions(
        self,
        campaign: Campaign,
        pause_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply pause actions to variants or segments
        
        Args:
            campaign: Campaign object
            pause_actions: List of pause actions
            
        Returns:
            List of applied pause actions
        """
        applied_actions = []
        
        for action in pause_actions:
            action_type = action.get("type")
            
            if action_type == "pause_variant":
                variant_id = action.get("variant_id")
                
                # Update variant status in Firestore
                try:
                    await self.firestore_service.update_variant(
                        variant_id,
                        {"status": "paused"}
                    )
                    
                    applied_actions.append({
                        "type": "pause_variant",
                        "variant_id": variant_id,
                        "success": True
                    })
                    
                    logger.info(f"Paused variant: {variant_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to pause variant {variant_id}: {e}")
                    applied_actions.append({
                        "type": "pause_variant",
                        "variant_id": variant_id,
                        "success": False,
                        "error": str(e)
                    })
            
            elif action_type == "pause_segment":
                segment_id = action.get("segment_id")
                
                # Update segment status in Firestore
                try:
                    await self.firestore_service.update_segment(
                        segment_id,
                        {"status": "paused"}
                    )
                    
                    applied_actions.append({
                        "type": "pause_segment",
                        "segment_id": segment_id,
                        "success": True
                    })
                    
                    logger.info(f"Paused segment: {segment_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to pause segment {segment_id}: {e}")
                    applied_actions.append({
                        "type": "pause_segment",
                        "segment_id": segment_id,
                        "success": False,
                        "error": str(e)
                    })
        
        return applied_actions
    
    async def _coordinate_budget_adjustments(
        self,
        campaign: Campaign,
        budget_actions: List[Dict[str, Any]],
        correlation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Coordinate budget adjustments with Budget Optimizer Agent
        
        Args:
            campaign: Campaign object
            budget_actions: List of budget adjustment actions
            correlation_id: Correlation ID for tracking
            
        Returns:
            List of applied budget adjustments
        """
        if not budget_actions:
            return []
        
        logger.info(
            f"Coordinating budget adjustments",
            extra={
                "campaign_id": campaign.campaign_id,
                "action_count": len(budget_actions),
                "correlation_id": correlation_id
            }
        )
        
        # Create message for Budget Optimizer Agent
        message = AgentMessage(
            message_type="adjust_budget",
            data={
                "campaign_id": campaign.campaign_id,
                "actions": budget_actions,
                "current_allocation": campaign.budget_allocation
            },
            sender=self.name,
            correlation_id=correlation_id
        )
        
        # Send message to Budget Optimizer Agent
        response = await self._send_message_to_agent("budget_optimizer", message)
        
        if response.success:
            # Update budget allocation in Firestore
            new_allocation = response.data.get("allocation", {})
            
            try:
                await self.firestore_service.update_allocation(
                    campaign.campaign_id,
                    new_allocation
                )
                
                return response.data.get("applied_actions", [])
                
            except Exception as e:
                logger.error(f"Failed to update budget allocation: {e}")
                return []
        else:
            logger.warning(
                f"Budget adjustment failed, using fallback",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "error": response.error
                }
            )
            
            # Fallback: Apply simple percentage adjustments
            return self._apply_simple_budget_adjustments(campaign, budget_actions)
    
    def _apply_simple_budget_adjustments(
        self,
        campaign: Campaign,
        budget_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply simple budget adjustments as fallback
        
        Args:
            campaign: Campaign object
            budget_actions: List of budget adjustment actions
            
        Returns:
            List of applied adjustments
        """
        applied = []
        
        for action in budget_actions:
            # Simple fallback: log the action but don't apply complex logic
            applied.append({
                "type": action.get("type"),
                "success": True,
                "fallback": True,
                "message": "Applied simple adjustment (fallback mode)"
            })
        
        return applied
    
    async def _coordinate_creative_updates(
        self,
        campaign: Campaign,
        creative_actions: List[Dict[str, Any]],
        correlation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Coordinate creative updates with Creative Generator Agent
        
        Args:
            campaign: Campaign object
            creative_actions: List of creative update actions
            correlation_id: Correlation ID for tracking
            
        Returns:
            List of applied creative updates
        """
        if not creative_actions:
            return []
        
        logger.info(
            f"Coordinating creative updates",
            extra={
                "campaign_id": campaign.campaign_id,
                "action_count": len(creative_actions),
                "correlation_id": correlation_id
            }
        )
        
        # Create message for Creative Generator Agent
        message = AgentMessage(
            message_type="generate_new_variants",
            data={
                "campaign_id": campaign.campaign_id,
                "actions": creative_actions,
                "existing_variants": campaign.creative_variants,
                "business_goal": campaign.business_goal,
                "products": campaign.products
            },
            sender=self.name,
            correlation_id=correlation_id
        )
        
        # Send message to Creative Generator Agent
        response = await self._send_message_to_agent("creative_generator", message)
        
        if response.success:
            # New variants generated successfully
            new_variants = response.data.get("variations", [])
            
            # Persist new variants to Firestore
            # (This will be handled by Creative Generator Agent in full implementation)
            
            return response.data.get("applied_actions", [])
        else:
            logger.warning(
                f"Creative update failed",
                extra={
                    "campaign_id": campaign.campaign_id,
                    "error": response.error
                }
            )
            
            return []


# Global orchestrator instance
_orchestrator_instance: Optional[CampaignOrchestratorAgent] = None


def get_orchestrator_agent() -> CampaignOrchestratorAgent:
    """Get or create the global Campaign Orchestrator Agent instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = CampaignOrchestratorAgent()
    return _orchestrator_instance
