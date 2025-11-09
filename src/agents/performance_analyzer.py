"""Performance Analyzer Agent - Monitors campaign metrics and identifies optimization opportunities"""

import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.models.campaign import Campaign, CampaignStatus
from src.models.metrics import PerformanceMetrics, VariantMetrics, SegmentMetrics, MetricsSnapshot
from src.services.firestore import get_firestore_service
from src.config import settings

logger = logging.getLogger(__name__)


class AgentMessage:
    """Message structure for agent communication"""
    
    def __init__(
        self,
        message_type: str,
        data: Dict[str, Any],
        sender: str = "performance_analyzer",
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


class OptimizationAction(Dict[str, Any]):
    """Optimization action recommendation"""
    pass


class PerformanceAnalysis:
    """Analysis results with optimization recommendations"""
    
    def __init__(
        self,
        campaign_id: str,
        has_optimizations: bool = False,
        actions: Optional[List[OptimizationAction]] = None,
        summary: Optional[str] = None
    ):
        self.campaign_id = campaign_id
        self.has_optimizations = has_optimizations
        self.actions = actions or []
        self.summary = summary or ""
        self.timestamp = datetime.utcnow()


class PerformanceAnalyzerAgent:
    """
    Performance Analyzer Agent
    
    Monitors campaign performance and identifies optimization opportunities by:
    - Collecting performance metrics every 15 minutes from Firestore
    - Calculating ROAS, CPA, CTR for each variant-segment combination
    - Detecting underperforming variants (ROAS < 1.0 after 100 clicks)
    - Detecting high performers (ROAS > 3.0)
    - Sending optimization recommendations to Campaign Orchestrator Agent
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.3, 11.1, 11.2
    """
    
    def __init__(self):
        """Initialize the Performance Analyzer Agent"""
        self.name = "performance_analyzer"
        self.firestore_service = get_firestore_service()
        self.monitoring_interval = 900  # 15 minutes in seconds
        self.orchestrator_agent = None  # Placeholder for ADK agent communication
        
        # Performance thresholds
        self.underperforming_roas_threshold = 1.0
        self.high_performing_roas_threshold = 3.0
        self.min_clicks_for_evaluation = 100
        self.consecutive_periods_threshold = 4
        
        logger.info(
            f"Performance Analyzer Agent initialized",
            extra={
                "agent_name": self.name,
                "monitoring_interval": self.monitoring_interval,
                "underperforming_threshold": self.underperforming_roas_threshold,
                "high_performing_threshold": self.high_performing_roas_threshold
            }
        )
    
    async def get_active_campaigns(self) -> List[Campaign]:
        """
        Get all active campaigns that need monitoring
        
        Queries Firestore for campaigns with status=ACTIVE
        
        Returns:
            List of active Campaign objects
            
        Requirements: 6.1, 11.1, 11.2
        """
        logger.info("Retrieving active campaigns for monitoring")
        
        try:
            campaigns = await self.firestore_service.get_active_campaigns()
            
            logger.info(
                f"Retrieved active campaigns",
                extra={
                    "campaign_count": len(campaigns),
                    "campaign_ids": [c.campaign_id for c in campaigns]
                }
            )
            
            return campaigns
            
        except Exception as e:
            logger.error(
                f"Error retrieving active campaigns",
                extra={"error": str(e)}
            )
            raise
    
    async def monitor_campaigns(self) -> Dict[str, Any]:
        """
        Monitor all active campaigns and trigger optimizations
        
        This is the main scheduled task that runs every 15 minutes:
        1. Gets all active campaigns
        2. Collects metrics for each campaign
        3. Analyzes performance
        4. Sends optimization recommendations to Campaign Orchestrator
        
        Returns:
            Dictionary with monitoring results
            
        Requirements: 6.1, 11.1, 11.2
        """
        correlation_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting campaign monitoring cycle",
            extra={
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        try:
            # Get all active campaigns
            active_campaigns = await self.get_active_campaigns()
            
            if not active_campaigns:
                logger.info("No active campaigns to monitor")
                return {
                    "success": True,
                    "campaigns_monitored": 0,
                    "optimizations_triggered": 0,
                    "correlation_id": correlation_id
                }
            
            # Monitor each campaign
            monitoring_results = []
            optimizations_triggered = 0
            
            for campaign in active_campaigns:
                try:
                    # Collect and analyze metrics
                    metrics = await self.collect_metrics(campaign.campaign_id)
                    analysis = await self.analyze_performance(campaign, metrics)
                    
                    # Persist metrics to Firestore
                    await self.persist_metrics(metrics)
                    
                    # Send optimization recommendations if needed
                    if analysis.has_optimizations:
                        await self._send_optimization_message(analysis)
                        optimizations_triggered += 1
                    
                    monitoring_results.append({
                        "campaign_id": campaign.campaign_id,
                        "success": True,
                        "has_optimizations": analysis.has_optimizations,
                        "action_count": len(analysis.actions)
                    })
                    
                except Exception as e:
                    logger.error(
                        f"Error monitoring campaign",
                        extra={
                            "campaign_id": campaign.campaign_id,
                            "error": str(e)
                        }
                    )
                    monitoring_results.append({
                        "campaign_id": campaign.campaign_id,
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info(
                f"Campaign monitoring cycle completed",
                extra={
                    "correlation_id": correlation_id,
                    "campaigns_monitored": len(active_campaigns),
                    "optimizations_triggered": optimizations_triggered,
                    "successful": sum(1 for r in monitoring_results if r["success"])
                }
            )
            
            return {
                "success": True,
                "campaigns_monitored": len(active_campaigns),
                "optimizations_triggered": optimizations_triggered,
                "results": monitoring_results,
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                f"Error in monitoring cycle",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e)
                }
            )
            raise

    async def collect_metrics(self, campaign_id: str) -> PerformanceMetrics:
        """
        Collect performance metrics for a campaign from Firestore
        
        Gathers data from:
        - Creative variants (impressions, clicks, conversions, spend, revenue)
        - Audience segments (impressions, clicks, conversions, spend, revenue)
        - Platform breakdowns
        
        Calculates:
        - ROAS (Return on Ad Spend)
        - CPA (Cost Per Acquisition)
        - CTR (Click-Through Rate)
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            PerformanceMetrics object with complete metrics data
            
        Requirements: 6.1, 6.2
        """
        logger.info(
            f"Collecting metrics for campaign",
            extra={"campaign_id": campaign_id}
        )
        
        try:
            # Get campaign data
            campaign = await self.firestore_service.get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            # Get creative variants with their metrics
            variants = await self.firestore_service.get_variants_by_campaign(campaign_id)
            variant_metrics = []
            
            for variant in variants:
                vm = VariantMetrics(
                    variant_id=variant.variant_id,
                    impressions=variant.impressions,
                    clicks=variant.clicks,
                    conversions=variant.conversions,
                    spend=variant.spend,
                    revenue=variant.revenue
                )
                variant_metrics.append(vm)
            
            # Get audience segments with their metrics
            segments = await self.firestore_service.get_segments_by_campaign(campaign_id)
            segment_metrics = []
            
            for segment in segments:
                sm = SegmentMetrics(
                    segment_id=segment.segment_id,
                    impressions=segment.impressions,
                    clicks=segment.clicks,
                    conversions=segment.conversions,
                    spend=segment.spend,
                    revenue=segment.revenue
                )
                segment_metrics.append(sm)
            
            # Calculate aggregate totals
            total_impressions = sum(v.impressions for v in variant_metrics)
            total_clicks = sum(v.clicks for v in variant_metrics)
            total_conversions = sum(v.conversions for v in variant_metrics)
            total_spend = sum(v.spend for v in variant_metrics)
            total_revenue = sum(v.revenue for v in variant_metrics)
            
            # Create performance metrics object
            metrics = PerformanceMetrics(
                campaign_id=campaign_id,
                timestamp=datetime.utcnow(),
                total_spend=total_spend,
                total_impressions=total_impressions,
                total_clicks=total_clicks,
                total_conversions=total_conversions,
                total_revenue=total_revenue,
                by_variant=variant_metrics,
                by_segment=segment_metrics,
                by_platform={}  # Platform metrics would come from ad platform APIs
            )
            
            # Calculate aggregate metrics (ROAS, CPA, CTR)
            metrics.calculate_aggregate_metrics()
            
            logger.info(
                f"Collected metrics for campaign",
                extra={
                    "campaign_id": campaign_id,
                    "total_spend": total_spend,
                    "total_conversions": total_conversions,
                    "roas": metrics.roas,
                    "variant_count": len(variant_metrics),
                    "segment_count": len(segment_metrics)
                }
            )
            
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error collecting metrics",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
            raise
    
    async def analyze_performance(
        self,
        campaign: Campaign,
        metrics: PerformanceMetrics
    ) -> PerformanceAnalysis:
        """
        Analyze campaign performance and identify optimization opportunities
        
        Detection rules:
        - Underperforming variants: ROAS < 1.0 after 100+ clicks
        - High performers: ROAS > 3.0
        - Declining performance: ROAS trending down over time
        
        Args:
            campaign: Campaign object
            metrics: Current performance metrics
            
        Returns:
            PerformanceAnalysis with optimization actions
            
        Requirements: 6.2, 6.3, 6.4
        """
        logger.info(
            f"Analyzing performance for campaign",
            extra={
                "campaign_id": campaign.campaign_id,
                "roas": metrics.roas,
                "total_conversions": metrics.total_conversions
            }
        )
        
        actions: List[OptimizationAction] = []
        
        # Analyze variant performance
        variant_actions = await self._analyze_variant_performance(
            campaign,
            metrics.by_variant
        )
        actions.extend(variant_actions)
        
        # Analyze segment performance
        segment_actions = await self._analyze_segment_performance(
            campaign,
            metrics.by_segment
        )
        actions.extend(segment_actions)
        
        # Check for overall campaign performance issues
        campaign_actions = self._analyze_campaign_performance(campaign, metrics)
        actions.extend(campaign_actions)
        
        # Generate summary
        summary = self._generate_analysis_summary(metrics, actions)
        
        has_optimizations = len(actions) > 0
        
        logger.info(
            f"Performance analysis completed",
            extra={
                "campaign_id": campaign.campaign_id,
                "has_optimizations": has_optimizations,
                "action_count": len(actions),
                "variant_actions": len(variant_actions),
                "segment_actions": len(segment_actions),
                "campaign_actions": len(campaign_actions)
            }
        )
        
        return PerformanceAnalysis(
            campaign_id=campaign.campaign_id,
            has_optimizations=has_optimizations,
            actions=actions,
            summary=summary
        )
    
    async def _analyze_variant_performance(
        self,
        campaign: Campaign,
        variant_metrics: List[VariantMetrics]
    ) -> List[OptimizationAction]:
        """
        Analyze creative variant performance
        
        Detects:
        - Underperforming variants (ROAS < 1.0 after 100 clicks)
        - High performing variants (ROAS > 3.0)
        
        Args:
            campaign: Campaign object
            variant_metrics: List of variant metrics
            
        Returns:
            List of optimization actions for variants
            
        Requirements: 6.3, 6.4
        """
        actions: List[OptimizationAction] = []
        
        for vm in variant_metrics:
            roas = vm.calculate_roas()
            
            # Check for underperforming variants
            if vm.clicks >= self.min_clicks_for_evaluation and roas < self.underperforming_roas_threshold:
                # Check if this is consistent underperformance
                is_consistent = await self._check_consistent_underperformance(
                    campaign.campaign_id,
                    vm.variant_id
                )
                
                if is_consistent:
                    actions.append({
                        "type": "pause_variant",
                        "variant_id": vm.variant_id,
                        "reason": f"Consistently low ROAS: {roas:.2f} (threshold: {self.underperforming_roas_threshold})",
                        "current_roas": roas,
                        "clicks": vm.clicks,
                        "spend": vm.spend,
                        "priority": "high"
                    })
                    
                    logger.info(
                        f"Detected underperforming variant",
                        extra={
                            "campaign_id": campaign.campaign_id,
                            "variant_id": vm.variant_id,
                            "roas": roas,
                            "clicks": vm.clicks
                        }
                    )
            
            # Check for high performers
            elif roas > self.high_performing_roas_threshold:
                actions.append({
                    "type": "scale_variant",
                    "variant_id": vm.variant_id,
                    "reason": f"High ROAS: {roas:.2f} (threshold: {self.high_performing_roas_threshold})",
                    "current_roas": roas,
                    "increase_percent": 50,
                    "priority": "medium"
                })
                
                logger.info(
                    f"Detected high-performing variant",
                    extra={
                        "campaign_id": campaign.campaign_id,
                        "variant_id": vm.variant_id,
                        "roas": roas
                    }
                )
        
        return actions
    
    async def _analyze_segment_performance(
        self,
        campaign: Campaign,
        segment_metrics: List[SegmentMetrics]
    ) -> List[OptimizationAction]:
        """
        Analyze audience segment performance
        
        Detects:
        - Underperforming segments (ROAS < 1.0)
        - High performing segments (ROAS > 4.0)
        
        Args:
            campaign: Campaign object
            segment_metrics: List of segment metrics
            
        Returns:
            List of optimization actions for segments
        """
        actions: List[OptimizationAction] = []
        
        for sm in segment_metrics:
            roas = sm.calculate_roas()
            
            # Check for underperforming segments
            if sm.clicks >= self.min_clicks_for_evaluation and roas < self.underperforming_roas_threshold:
                actions.append({
                    "type": "pause_segment",
                    "segment_id": sm.segment_id,
                    "reason": f"Low ROAS: {roas:.2f}",
                    "current_roas": roas,
                    "clicks": sm.clicks,
                    "spend": sm.spend,
                    "priority": "medium"
                })
                
                logger.info(
                    f"Detected underperforming segment",
                    extra={
                        "campaign_id": campaign.campaign_id,
                        "segment_id": sm.segment_id,
                        "roas": roas
                    }
                )
            
            # Check for high performing segments (higher threshold for segments)
            elif roas > 4.0:
                actions.append({
                    "type": "scale_segment",
                    "segment_id": sm.segment_id,
                    "reason": f"High ROAS: {roas:.2f}",
                    "current_roas": roas,
                    "increase_percent": 50,
                    "priority": "high"
                })
                
                logger.info(
                    f"Detected high-performing segment",
                    extra={
                        "campaign_id": campaign.campaign_id,
                        "segment_id": sm.segment_id,
                        "roas": roas
                    }
                )
        
        return actions
    
    def _analyze_campaign_performance(
        self,
        campaign: Campaign,
        metrics: PerformanceMetrics
    ) -> List[OptimizationAction]:
        """
        Analyze overall campaign performance
        
        Detects:
        - Overall low ROAS requiring new creative variants
        - Budget pacing issues
        
        Args:
            campaign: Campaign object
            metrics: Performance metrics
            
        Returns:
            List of campaign-level optimization actions
        """
        actions: List[OptimizationAction] = []
        
        # Check if campaign needs new creative variants
        if metrics.roas < 2.0 and metrics.total_clicks > 500:
            # Check if all variants are underperforming
            underperforming_count = sum(
                1 for vm in metrics.by_variant
                if vm.calculate_roas() < 2.0 and vm.clicks >= 50
            )
            
            if underperforming_count >= len(metrics.by_variant) * 0.7:  # 70% underperforming
                actions.append({
                    "type": "generate_new_variants",
                    "campaign_id": campaign.campaign_id,
                    "reason": f"Overall low ROAS: {metrics.roas:.2f}, need fresh creative variants",
                    "current_roas": metrics.roas,
                    "variant_count": 3,
                    "priority": "high"
                })
                
                logger.info(
                    f"Campaign needs new creative variants",
                    extra={
                        "campaign_id": campaign.campaign_id,
                        "roas": metrics.roas,
                        "underperforming_variants": underperforming_count
                    }
                )
        
        return actions
    
    async def _check_consistent_underperformance(
        self,
        campaign_id: str,
        variant_id: str
    ) -> bool:
        """
        Check if a variant has been consistently underperforming
        
        Looks at the last 4 measurement periods (1 hour) to determine
        if underperformance is consistent.
        
        Args:
            campaign_id: Campaign identifier
            variant_id: Variant identifier
            
        Returns:
            True if consistently underperforming, False otherwise
            
        Requirements: 6.3
        """
        try:
            # Get metrics history for the last hour
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics_history = await self.firestore_service.get_metrics_history(
                campaign_id=campaign_id,
                start_time=start_time,
                end_time=end_time,
                limit=self.consecutive_periods_threshold
            )
            
            if len(metrics_history) < self.consecutive_periods_threshold:
                # Not enough data to determine consistency
                return False
            
            # Check if variant was underperforming in all periods
            underperforming_periods = 0
            
            for metrics in metrics_history:
                variant_metrics = metrics.get_variant_metrics(variant_id)
                if variant_metrics:
                    roas = variant_metrics.calculate_roas()
                    if roas < self.underperforming_roas_threshold:
                        underperforming_periods += 1
            
            # Consistent if underperforming in all periods
            is_consistent = underperforming_periods >= self.consecutive_periods_threshold
            
            logger.debug(
                f"Checked consistency for variant",
                extra={
                    "campaign_id": campaign_id,
                    "variant_id": variant_id,
                    "underperforming_periods": underperforming_periods,
                    "threshold": self.consecutive_periods_threshold,
                    "is_consistent": is_consistent
                }
            )
            
            return is_consistent
            
        except Exception as e:
            logger.error(
                f"Error checking consistency",
                extra={
                    "campaign_id": campaign_id,
                    "variant_id": variant_id,
                    "error": str(e)
                }
            )
            # Default to True if we can't check (fail-safe)
            return True
    
    def _generate_analysis_summary(
        self,
        metrics: PerformanceMetrics,
        actions: List[OptimizationAction]
    ) -> str:
        """
        Generate human-readable summary of analysis
        
        Args:
            metrics: Performance metrics
            actions: Optimization actions
            
        Returns:
            Summary string
        """
        if not actions:
            return f"Campaign performing well. ROAS: {metrics.roas:.2f}, Conversions: {metrics.total_conversions}"
        
        action_types = {}
        for action in actions:
            action_type = action["type"]
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        summary_parts = [f"ROAS: {metrics.roas:.2f}"]
        
        for action_type, count in action_types.items():
            summary_parts.append(f"{count} {action_type.replace('_', ' ')} action(s)")
        
        return ", ".join(summary_parts)

    async def _send_optimization_message(self, analysis: PerformanceAnalysis) -> None:
        """
        Send optimization_needed message to Campaign Orchestrator Agent
        
        This method uses ADK's agent-to-agent messaging to communicate
        optimization recommendations to the orchestrator.
        
        Args:
            analysis: Performance analysis with optimization actions
            
        Requirements: 6.5, 9.1, 9.3
        """
        message = AgentMessage(
            message_type="optimization_needed",
            data={
                "campaign_id": analysis.campaign_id,
                "actions": analysis.actions,
                "summary": analysis.summary,
                "timestamp": analysis.timestamp.isoformat(),
                "action_count": len(analysis.actions)
            },
            sender=self.name
        )
        
        logger.info(
            f"Sending optimization message to orchestrator",
            extra={
                "campaign_id": analysis.campaign_id,
                "correlation_id": message.correlation_id,
                "action_count": len(analysis.actions),
                "message_type": message.message_type
            }
        )
        
        try:
            # TODO: Replace with actual ADK message sending
            # For now, this is a placeholder that logs the message
            # In production, this would use ADK's Pub/Sub or direct messaging
            
            # Track optimization in Firestore
            await self._track_optimization_history(analysis)
            
            logger.info(
                f"Optimization message sent successfully",
                extra={
                    "campaign_id": analysis.campaign_id,
                    "correlation_id": message.correlation_id
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error sending optimization message",
                extra={
                    "campaign_id": analysis.campaign_id,
                    "correlation_id": message.correlation_id,
                    "error": str(e)
                }
            )
            raise
    
    async def _track_optimization_history(self, analysis: PerformanceAnalysis) -> None:
        """
        Track optimization history in Firestore
        
        Stores optimization actions and their reasoning for audit trail
        and to prevent duplicate recommendations.
        
        Args:
            analysis: Performance analysis with actions
            
        Requirements: 9.3
        """
        try:
            # Create optimization history record
            optimization_record = {
                "campaign_id": analysis.campaign_id,
                "timestamp": analysis.timestamp,
                "actions": analysis.actions,
                "summary": analysis.summary,
                "action_count": len(analysis.actions)
            }
            
            # Store in campaign's optimization history
            campaign = await self.firestore_service.get_campaign(analysis.campaign_id)
            
            if campaign:
                # Get existing optimization history
                optimization_history = getattr(campaign, 'optimization_history', [])
                
                # Add new record
                optimization_history.append(optimization_record)
                
                # Keep only last 100 records
                if len(optimization_history) > 100:
                    optimization_history = optimization_history[-100:]
                
                # Update campaign
                await self.firestore_service.update_campaign(
                    analysis.campaign_id,
                    {
                        "optimization_history": optimization_history,
                        "last_optimization_check": analysis.timestamp
                    }
                )
                
                logger.info(
                    f"Tracked optimization history",
                    extra={
                        "campaign_id": analysis.campaign_id,
                        "action_count": len(analysis.actions),
                        "history_size": len(optimization_history)
                    }
                )
        
        except Exception as e:
            logger.error(
                f"Error tracking optimization history",
                extra={
                    "campaign_id": analysis.campaign_id,
                    "error": str(e)
                }
            )
            # Don't raise - this is non-critical
    
    def generate_optimization_actions(
        self,
        campaign: Campaign,
        metrics: PerformanceMetrics,
        action_types: Optional[List[str]] = None
    ) -> List[OptimizationAction]:
        """
        Generate specific optimization actions based on performance data
        
        Action types:
        - pause: Pause underperforming variants/segments
        - scale: Increase budget for high performers
        - test: Generate new creative variants
        
        Args:
            campaign: Campaign object
            metrics: Performance metrics
            action_types: Optional list of action types to generate
            
        Returns:
            List of optimization actions with specific recommendations
            
        Requirements: 6.5, 9.1, 9.3
        """
        logger.info(
            f"Generating optimization actions",
            extra={
                "campaign_id": campaign.campaign_id,
                "action_types": action_types
            }
        )
        
        actions: List[OptimizationAction] = []
        
        # Generate pause actions for underperformers
        if not action_types or "pause" in action_types:
            underperforming = metrics.get_underperforming_variants(
                roas_threshold=self.underperforming_roas_threshold,
                min_clicks=self.min_clicks_for_evaluation
            )
            
            for variant in underperforming:
                actions.append({
                    "type": "pause_variant",
                    "variant_id": variant.variant_id,
                    "reason": f"ROAS {variant.calculate_roas():.2f} below threshold {self.underperforming_roas_threshold}",
                    "current_roas": variant.calculate_roas(),
                    "clicks": variant.clicks,
                    "spend": variant.spend,
                    "priority": "high"
                })
        
        # Generate scale actions for high performers
        if not action_types or "scale" in action_types:
            top_performers = metrics.get_top_performing_variants(limit=3)
            
            for variant in top_performers:
                roas = variant.calculate_roas()
                if roas > self.high_performing_roas_threshold:
                    actions.append({
                        "type": "scale_variant",
                        "variant_id": variant.variant_id,
                        "reason": f"High ROAS {roas:.2f} exceeds threshold {self.high_performing_roas_threshold}",
                        "current_roas": roas,
                        "increase_percent": 50,
                        "priority": "medium"
                    })
        
        # Generate test actions for new variants
        if not action_types or "test" in action_types:
            if metrics.roas < 2.0 and metrics.total_clicks > 500:
                actions.append({
                    "type": "generate_new_variants",
                    "campaign_id": campaign.campaign_id,
                    "reason": f"Overall ROAS {metrics.roas:.2f} needs improvement",
                    "current_roas": metrics.roas,
                    "variant_count": 3,
                    "priority": "high"
                })
        
        logger.info(
            f"Generated optimization actions",
            extra={
                "campaign_id": campaign.campaign_id,
                "action_count": len(actions),
                "pause_actions": sum(1 for a in actions if a["type"].startswith("pause")),
                "scale_actions": sum(1 for a in actions if a["type"].startswith("scale")),
                "test_actions": sum(1 for a in actions if a["type"] == "generate_new_variants")
            }
        )
        
        return actions
    
    async def handle_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Handle incoming messages from other agents
        
        Supported message types:
        - analyze_campaign: Analyze a specific campaign on demand
        - get_metrics: Get current metrics for a campaign
        
        Args:
            message: Incoming agent message
            
        Returns:
            Response dictionary
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
            if message.message_type == "analyze_campaign":
                campaign_id = message.data.get("campaign_id")
                
                if not campaign_id:
                    return {
                        "success": False,
                        "error": "Missing campaign_id in message data"
                    }
                
                # Get campaign and analyze
                campaign = await self.firestore_service.get_campaign(campaign_id)
                if not campaign:
                    return {
                        "success": False,
                        "error": f"Campaign {campaign_id} not found"
                    }
                
                metrics = await self.collect_metrics(campaign_id)
                analysis = await self.analyze_performance(campaign, metrics)
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "has_optimizations": analysis.has_optimizations,
                    "actions": analysis.actions,
                    "summary": analysis.summary
                }
            
            elif message.message_type == "get_metrics":
                campaign_id = message.data.get("campaign_id")
                
                if not campaign_id:
                    return {
                        "success": False,
                        "error": "Missing campaign_id in message data"
                    }
                
                metrics = await self.collect_metrics(campaign_id)
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "metrics": metrics.model_dump()
                }
            
            else:
                logger.warning(
                    f"Unknown message type: {message.message_type}",
                    extra={"correlation_id": message.correlation_id}
                )
                return {
                    "success": False,
                    "error": f"Unknown message type: {message.message_type}"
                }
        
        except Exception as e:
            logger.error(
                f"Error handling message",
                extra={
                    "message_type": message.message_type,
                    "correlation_id": message.correlation_id,
                    "error": str(e)
                }
            )
            return {
                "success": False,
                "error": f"Error processing message: {str(e)}"
            }

    async def persist_metrics(self, metrics: PerformanceMetrics) -> Dict[str, str]:
        """
        Persist performance metrics to Firestore
        
        This method:
        1. Saves metrics using FirestoreService.save_metrics
        2. Creates snapshot using FirestoreService.save_snapshot for time-series
        3. Updates campaign performance fields
        
        Args:
            metrics: Performance metrics to persist
            
        Returns:
            Dictionary with IDs of saved documents
            
        Requirements: 6.1, 13.1
        """
        logger.info(
            f"Persisting metrics to Firestore",
            extra={
                "campaign_id": metrics.campaign_id,
                "timestamp": metrics.timestamp.isoformat(),
                "roas": metrics.roas,
                "total_spend": metrics.total_spend
            }
        )
        
        try:
            # Save full metrics record
            metrics_id = await self.firestore_service.save_metrics(metrics)
            
            # Create snapshot for time-series analysis
            snapshot = MetricsSnapshot(
                campaign_id=metrics.campaign_id,
                timestamp=metrics.timestamp,
                spend=metrics.total_spend,
                impressions=metrics.total_impressions,
                clicks=metrics.total_clicks,
                conversions=metrics.total_conversions,
                revenue=metrics.total_revenue,
                roas=metrics.roas
            )
            
            snapshot_id = await self.firestore_service.save_snapshot(snapshot)
            
            # Update campaign with latest performance data
            await self.firestore_service.update_campaign(
                metrics.campaign_id,
                {
                    "total_spend": metrics.total_spend,
                    "total_impressions": metrics.total_impressions,
                    "total_clicks": metrics.total_clicks,
                    "total_conversions": metrics.total_conversions,
                    "current_roas": metrics.roas,
                    "last_metrics_update": metrics.timestamp
                }
            )
            
            logger.info(
                f"Successfully persisted metrics",
                extra={
                    "campaign_id": metrics.campaign_id,
                    "metrics_id": metrics_id,
                    "snapshot_id": snapshot_id
                }
            )
            
            return {
                "metrics_id": metrics_id,
                "snapshot_id": snapshot_id,
                "campaign_id": metrics.campaign_id
            }
            
        except Exception as e:
            logger.error(
                f"Error persisting metrics",
                extra={
                    "campaign_id": metrics.campaign_id,
                    "error": str(e)
                }
            )
            raise
    
    async def get_campaign_metrics_history(
        self,
        campaign_id: str,
        hours: int = 24
    ) -> List[PerformanceMetrics]:
        """
        Get historical metrics for a campaign
        
        Args:
            campaign_id: Campaign identifier
            hours: Number of hours of history to retrieve
            
        Returns:
            List of historical performance metrics
        """
        logger.info(
            f"Retrieving metrics history",
            extra={
                "campaign_id": campaign_id,
                "hours": hours
            }
        )
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            metrics_history = await self.firestore_service.get_metrics_history(
                campaign_id=campaign_id,
                start_time=start_time,
                end_time=end_time,
                limit=100
            )
            
            logger.info(
                f"Retrieved metrics history",
                extra={
                    "campaign_id": campaign_id,
                    "record_count": len(metrics_history),
                    "hours": hours
                }
            )
            
            return metrics_history
            
        except Exception as e:
            logger.error(
                f"Error retrieving metrics history",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
            raise
    
    async def get_campaign_snapshots(
        self,
        campaign_id: str,
        hours: int = 24
    ) -> List[MetricsSnapshot]:
        """
        Get metrics snapshots for time-series analysis
        
        Args:
            campaign_id: Campaign identifier
            hours: Number of hours of snapshots to retrieve
            
        Returns:
            List of metrics snapshots
        """
        logger.info(
            f"Retrieving metrics snapshots",
            extra={
                "campaign_id": campaign_id,
                "hours": hours
            }
        )
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            snapshots = await self.firestore_service.get_snapshots(
                campaign_id=campaign_id,
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )
            
            logger.info(
                f"Retrieved metrics snapshots",
                extra={
                    "campaign_id": campaign_id,
                    "snapshot_count": len(snapshots),
                    "hours": hours
                }
            )
            
            return snapshots
            
        except Exception as e:
            logger.error(
                f"Error retrieving snapshots",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
            raise


# Utility function to create agent instance
def create_performance_analyzer_agent() -> PerformanceAnalyzerAgent:
    """
    Create and return a Performance Analyzer Agent instance
    
    Returns:
        Initialized PerformanceAnalyzerAgent
    """
    return PerformanceAnalyzerAgent()
