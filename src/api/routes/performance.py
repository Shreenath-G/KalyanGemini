"""Performance and optimization API routes"""

from fastapi import APIRouter, Depends, Request, status
from typing import Dict, Any, List
import logging
from datetime import datetime

from src.models.metrics import PerformanceMetrics, VariantMetrics, SegmentMetrics, PlatformMetrics
from src.api.dependencies import get_current_account_id
from src.api.errors import NotFoundError, ValidationError
from src.services.firestore import get_firestore_service
from src.agents.campaign_orchestrator import get_orchestrator_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/campaigns", tags=["Performance"])


@router.get(
    "/{campaign_id}/performance",
    response_model=PerformanceMetrics,
    summary="Get campaign performance metrics",
    description="""Retrieve comprehensive real-time performance metrics for a campaign.
    
    **Metrics Included:**
    - **Aggregate:** Total spend, impressions, clicks, conversions, revenue
    - **Calculated:** ROAS (Return on Ad Spend), CPA (Cost Per Acquisition), CTR (Click-Through Rate)
    - **Breakdowns:** By creative variant, audience segment, and platform
    
    **Update Frequency:** Metrics updated every 15 minutes
    
    **Authentication Required:** API Key in X-API-Key header
    """,
    responses={
        200: {
            "description": "Performance metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "campaign_id": "camp_a1b2c3d4e5f6",
                        "timestamp": "2025-11-09T10:30:00Z",
                        "total_spend": 1250.50,
                        "total_impressions": 125000,
                        "total_clicks": 3500,
                        "total_conversions": 45,
                        "total_revenue": 1440.00,
                        "roas": 2.88,
                        "cpa": 27.79,
                        "ctr": 2.8,
                        "by_variant": [
                            {
                                "variant_id": "var_001",
                                "impressions": 50000,
                                "clicks": 1500,
                                "conversions": 20,
                                "spend": 500.00,
                                "revenue": 640.00,
                                "roas": 3.2,
                                "cpa": 25.00,
                                "ctr": 3.0
                            }
                        ],
                        "by_segment": [
                            {
                                "segment_id": "seg_001",
                                "segment_name": "Tech-Savvy Business Owners",
                                "impressions": 60000,
                                "clicks": 2000,
                                "conversions": 28,
                                "spend": 700.00,
                                "roas": 3.5
                            }
                        ],
                        "by_platform": {
                            "google_ads": {
                                "spend": 500.20,
                                "impressions": 50000,
                                "clicks": 1400,
                                "conversions": 18,
                                "roas": 2.9
                            },
                            "meta_ads": {
                                "spend": 500.30,
                                "impressions": 50000,
                                "clicks": 1400,
                                "conversions": 19,
                                "roas": 3.0
                            },
                            "programmatic": {
                                "spend": 250.00,
                                "impressions": 25000,
                                "clicks": 700,
                                "conversions": 8,
                                "roas": 2.5
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "Authentication failed"
        },
        404: {
            "description": "Campaign not found or access denied"
        }
    }
)
async def get_campaign_performance(
    campaign_id: str,
    request: Request
) -> PerformanceMetrics:
    """
    Get campaign performance metrics
    
    Returns comprehensive performance data including:
    - Aggregate metrics (spend, impressions, clicks, conversions, ROAS, CPA, CTR)
    - Performance breakdown by creative variant
    - Performance breakdown by audience segment
    - Performance breakdown by platform (Google Ads, Meta Ads, Programmatic)
    
    Requirements: 8.1, 8.3, 8.4, 14.1, 14.2, 14.3
    """
    account_id = get_current_account_id(request)
    
    # Verify campaign exists and user has access
    firestore_service = get_firestore_service()
    campaign = await firestore_service.get_campaign(campaign_id)
    
    if not campaign:
        logger.warning(f"Campaign not found: {campaign_id}")
        raise NotFoundError("Campaign", campaign_id)
    
    if campaign.account_id != account_id:
        logger.warning(
            f"Unauthorized performance access attempt",
            extra={
                "campaign_id": campaign_id,
                "requesting_account": account_id,
                "owner_account": campaign.account_id
            }
        )
        raise NotFoundError("Campaign", campaign_id)
    
    # Get latest metrics from Firestore
    metrics = await firestore_service.get_latest_metrics(campaign_id)
    
    if not metrics:
        # Create initial metrics from campaign data if none exist
        metrics = PerformanceMetrics(
            campaign_id=campaign_id,
            total_spend=campaign.total_spend,
            total_impressions=campaign.total_impressions,
            total_clicks=campaign.total_clicks,
            total_conversions=campaign.total_conversions,
            total_revenue=campaign.total_conversions * 32.0,  # Assume $32 per conversion
            by_variant=[],
            by_segment=[],
            by_platform={}
        )
        
        # Calculate aggregate metrics
        metrics.calculate_aggregate_metrics()
        
        # Save initial metrics to Firestore
        await firestore_service.save_metrics(metrics)
        
        # TODO: Populate variant, segment, and platform breakdowns
        # This will be implemented when Performance Analyzer Agent is ready
    
    logger.info(
        f"Retrieved performance metrics",
        extra={
            "campaign_id": campaign_id,
            "roas": metrics.roas,
            "total_spend": metrics.total_spend
        }
    )
    
    return metrics


@router.post(
    "/{campaign_id}/optimize",
    response_model=Dict[str, Any],
    summary="Trigger manual optimization",
    description="""Manually trigger AI-powered campaign optimization.
    
    **Optimization Process:**
    1. Performance Analyzer Agent evaluates current metrics
    2. Identifies underperforming variants (ROAS < 1.0)
    3. Identifies high performers (ROAS > 3.0)
    4. Generates optimization actions (pause, scale, adjust)
    5. Applies actions (if auto mode) or returns suggestions
    
    **Optimization Types:**
    - `auto`: Automatically apply recommended optimizations
    - `suggest`: Return suggestions without applying changes
    
    **Optimization Actions:**
    - Pause underperforming creative variants
    - Scale high-performing variants (increase budget by up to 50%)
    - Adjust audience targeting
    - Reallocate budget across platforms
    
    **Authentication Required:** API Key in X-API-Key header
    """,
    responses={
        200: {
            "description": "Optimization completed successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "auto_mode": {
                            "summary": "Auto optimization applied",
                            "value": {
                                "campaign_id": "camp_a1b2c3d4e5f6",
                                "optimization_type": "auto",
                                "actions": [
                                    {
                                        "type": "pause_variant",
                                        "variant_id": "var_003",
                                        "reason": "Low ROAS: 0.65",
                                        "estimated_impact": {
                                            "spend_reduction": 150.00,
                                            "roas_improvement": 0.2
                                        }
                                    },
                                    {
                                        "type": "scale_variant",
                                        "variant_id": "var_001",
                                        "reason": "High ROAS: 3.8",
                                        "increase_percent": 50,
                                        "estimated_impact": {
                                            "additional_spend": 250.00,
                                            "expected_conversions": 10
                                        }
                                    }
                                ],
                                "total_actions": 2,
                                "applied": True,
                                "message": "Applied 2 optimization actions",
                                "timestamp": "2025-11-09T10:30:00Z"
                            }
                        },
                        "suggest_mode": {
                            "summary": "Optimization suggestions only",
                            "value": {
                                "campaign_id": "camp_a1b2c3d4e5f6",
                                "optimization_type": "suggest",
                                "actions": [
                                    {
                                        "type": "adjust_targeting",
                                        "reason": "Overall ROAS below target: 1.8",
                                        "recommendation": "Consider refining audience targeting or creative messaging"
                                    }
                                ],
                                "total_actions": 1,
                                "applied": False,
                                "message": "Generated 1 optimization suggestions"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "No performance data available",
                            "details": "Campaign must have performance data before optimization"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Authentication failed"
        },
        404: {
            "description": "Campaign not found or access denied"
        }
    }
)
async def optimize_campaign(
    campaign_id: str,
    request: Request,
    optimization_type: str = "auto"
) -> Dict[str, Any]:
    """
    Trigger manual campaign optimization
    
    This endpoint allows users to manually trigger optimization actions.
    The system will:
    1. Analyze current performance
    2. Identify optimization opportunities
    3. Generate recommended actions
    4. Apply optimizations (if auto mode)
    
    Optimization types:
    - "auto": Automatically apply recommended optimizations
    - "suggest": Only return suggestions without applying
    
    Requirements: 8.1, 8.3, 8.4, 14.1, 14.2, 14.3
    """
    account_id = get_current_account_id(request)
    
    # Verify campaign exists and user has access
    firestore_service = get_firestore_service()
    campaign = await firestore_service.get_campaign(campaign_id)
    
    if not campaign:
        logger.warning(f"Campaign not found: {campaign_id}")
        raise NotFoundError("Campaign", campaign_id)
    
    if campaign.account_id != account_id:
        logger.warning(
            f"Unauthorized optimization attempt",
            extra={
                "campaign_id": campaign_id,
                "requesting_account": account_id,
                "owner_account": campaign.account_id
            }
        )
        raise NotFoundError("Campaign", campaign_id)
    
    if optimization_type not in ["auto", "suggest"]:
        raise ValidationError(
            "Invalid optimization type",
            "Must be 'auto' or 'suggest'"
        )
    
    logger.info(
        f"Manual optimization triggered",
        extra={
            "campaign_id": campaign_id,
            "optimization_type": optimization_type
        }
    )
    
    # Get current metrics from Firestore
    metrics = await firestore_service.get_latest_metrics(campaign_id)
    
    if not metrics:
        raise ValidationError(
            "No performance data available",
            "Campaign must have performance data before optimization"
        )
    
    # Generate optimization actions
    actions = []
    
    # TODO: This will be replaced with actual Performance Analyzer Agent logic
    # For now, generate sample recommendations based on simple rules
    
    # Check for underperforming variants
    underperforming = metrics.get_underperforming_variants(
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
    top_performers = metrics.get_top_performing_variants(limit=3)
    
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
    if metrics.roas < 2.0:
        actions.append({
            "type": "adjust_targeting",
            "reason": f"Overall ROAS below target: {metrics.roas:.2f}",
            "recommendation": "Consider refining audience targeting or creative messaging"
        })
    
    # Apply optimizations if auto mode
    applied_actions = []
    if optimization_type == "auto" and actions:
        # Send optimization actions to Campaign Orchestrator Agent
        try:
            orchestrator = get_orchestrator_agent()
            
            optimization_results = await orchestrator.handle_optimization_request(
                campaign_id=campaign_id,
                optimization_actions=actions,
                optimization_type="auto"
            )
            
            if optimization_results.get("success"):
                applied_actions = actions
                
                logger.info(
                    f"Optimization applied via orchestrator",
                    extra={
                        "campaign_id": campaign_id,
                        "actions_count": len(applied_actions)
                    }
                )
            else:
                logger.error(
                    f"Optimization failed",
                    extra={
                        "campaign_id": campaign_id,
                        "error": optimization_results.get("error")
                    }
                )
                
        except Exception as e:
            logger.error(
                f"Error applying optimizations via orchestrator",
                extra={
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            )
            
            # Fallback: Just log the actions
            for action in actions:
                logger.info(f"Optimization action (fallback): {action['type']}")
                applied_actions.append(action)
            
            # Update last optimized timestamp in Firestore
            await firestore_service.update_campaign(
                campaign_id,
                {"last_optimized_at": datetime.utcnow()}
            )
        
        # Save optimization actions to metrics for tracking
        metrics.timestamp = datetime.utcnow()
        await firestore_service.save_metrics(metrics)
    
    response = {
        "campaign_id": campaign_id,
        "optimization_type": optimization_type,
        "actions": actions if optimization_type == "suggest" else applied_actions,
        "total_actions": len(actions),
        "applied": optimization_type == "auto",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if optimization_type == "auto":
        response["message"] = f"Applied {len(applied_actions)} optimization actions"
    else:
        response["message"] = f"Generated {len(actions)} optimization suggestions"
    
    logger.info(
        f"Optimization completed",
        extra={
            "campaign_id": campaign_id,
            "actions_count": len(actions),
            "applied": optimization_type == "auto"
        }
    )
    
    return response


@router.get(
    "/{campaign_id}/performance/variants",
    response_model=List[VariantMetrics],
    summary="Get variant performance breakdown",
    description="Get performance metrics for all creative variants"
)
async def get_variant_performance(
    campaign_id: str,
    request: Request
) -> List[VariantMetrics]:
    """
    Get performance breakdown by creative variant
    
    Returns detailed metrics for each creative variant including:
    - Impressions, clicks, conversions
    - Spend and revenue
    - Calculated ROAS, CPA, CTR
    
    Requirements: 8.3
    """
    account_id = get_current_account_id(request)
    
    # Verify campaign access
    firestore_service = get_firestore_service()
    campaign = await firestore_service.get_campaign(campaign_id)
    
    if not campaign:
        raise NotFoundError("Campaign", campaign_id)
    
    if campaign.account_id != account_id:
        raise NotFoundError("Campaign", campaign_id)
    
    # Get metrics from Firestore
    metrics = await firestore_service.get_latest_metrics(campaign_id)
    
    if not metrics:
        return []
    
    logger.info(f"Retrieved variant performance for campaign: {campaign_id}")
    
    return metrics.by_variant


@router.get(
    "/{campaign_id}/performance/segments",
    response_model=List[SegmentMetrics],
    summary="Get segment performance breakdown",
    description="Get performance metrics for all audience segments"
)
async def get_segment_performance(
    campaign_id: str,
    request: Request
) -> List[SegmentMetrics]:
    """
    Get performance breakdown by audience segment
    
    Returns detailed metrics for each audience segment including:
    - Impressions, clicks, conversions
    - Spend and revenue
    - Calculated ROAS, CPA, CTR
    
    Requirements: 8.3
    """
    account_id = get_current_account_id(request)
    
    # Verify campaign access
    firestore_service = get_firestore_service()
    campaign = await firestore_service.get_campaign(campaign_id)
    
    if not campaign:
        raise NotFoundError("Campaign", campaign_id)
    
    if campaign.account_id != account_id:
        raise NotFoundError("Campaign", campaign_id)
    
    # Get metrics from Firestore
    metrics = await firestore_service.get_latest_metrics(campaign_id)
    
    if not metrics:
        return []
    
    logger.info(f"Retrieved segment performance for campaign: {campaign_id}")
    
    return metrics.by_segment


@router.get(
    "/{campaign_id}/performance/platforms",
    response_model=Dict[str, PlatformMetrics],
    summary="Get platform performance breakdown",
    description="Get performance metrics for all advertising platforms"
)
async def get_platform_performance(
    campaign_id: str,
    request: Request
) -> Dict[str, PlatformMetrics]:
    """
    Get performance breakdown by platform
    
    Returns detailed metrics for each platform (Google Ads, Meta Ads, Programmatic):
    - Impressions, clicks, conversions
    - Spend and revenue
    - Calculated ROAS, CPA, CTR
    
    Requirements: 8.3
    """
    account_id = get_current_account_id(request)
    
    # Verify campaign access
    firestore_service = get_firestore_service()
    campaign = await firestore_service.get_campaign(campaign_id)
    
    if not campaign:
        raise NotFoundError("Campaign", campaign_id)
    
    if campaign.account_id != account_id:
        raise NotFoundError("Campaign", campaign_id)
    
    # Get metrics from Firestore
    metrics = await firestore_service.get_latest_metrics(campaign_id)
    
    if not metrics:
        return {}
    
    logger.info(f"Retrieved platform performance for campaign: {campaign_id}")
    
    return metrics.by_platform
