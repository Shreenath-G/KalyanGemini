"""Bidding API routes for real-time bid execution"""

from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict, Any
import logging

from src.models.bidding import (
    BidRequest,
    BidResponse,
    NoBidResponse,
    BidRequestStatus
)
from src.agents.bid_execution import get_bid_execution_agent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/bidding",
    tags=["Bidding"]
)


@router.post(
    "/bid-request",
    response_model=BidResponse | NoBidResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle real-time bid request",
    description="""Webhook endpoint for programmatic ad exchanges to submit real-time bid requests.
    
    **Performance Requirement:** Must respond within 100ms
    
    **Bid Evaluation Process:**
    1. Quick relevance check (inventory type, platform, format)
    2. User profile matching to audience segments
    3. Budget availability verification
    4. Optimal bid price calculation
    5. Return bid or no-bid response
    
    **Bid Price Calculation:**
    - Base price from segment max CPC
    - Adjusted for user conversion probability
    - Reduced if budget is low (<10% remaining)
    - Maintains 20-40% win rate target
    
    **Authentication:** Webhook signature verification (implementation-specific)
    """,
    responses={
        200: {
            "description": "Bid decision made successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "bid_submitted": {
                            "summary": "Bid submitted",
                            "value": {
                                "request_id": "bid_req_xyz789",
                                "bid_price": 2.35,
                                "campaign_id": "camp_a1b2c3d4e5f6",
                                "creative_id": "var_001",
                                "currency": "USD"
                            }
                        },
                        "no_bid": {
                            "summary": "No bid (not relevant)",
                            "value": {
                                "request_id": "bid_req_xyz789",
                                "reason": "No matching audience segment"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid bid request format"
        },
        500: {
            "description": "Internal error - returns no-bid to avoid timeout"
        }
    }
)
async def handle_bid_request(
    bid_request: BidRequest,
    request: Request
) -> BidResponse | NoBidResponse:
    """
    Handle incoming bid request from ad exchange
    
    This endpoint receives bid requests from programmatic ad exchanges
    and returns a bid response or no-bid response within 100ms.
    
    The Bid Execution Agent evaluates the opportunity by:
    1. Checking relevance to active campaigns
    2. Matching user profile to audience segments
    3. Verifying budget availability
    4. Calculating optimal bid price
    
    Args:
        bid_request: Bid request from ad exchange
        request: FastAPI request object
        
    Returns:
        BidResponse with bid price or NoBidResponse if not bidding
        
    Requirements: 7.1, 7.2, 7.3, 7.4, 14.1, 14.2, 14.3
    """
    logger.info(
        f"Received bid request",
        extra={
            "request_id": bid_request.request_id,
            "user_id": bid_request.user_profile.user_id,
            "platform": bid_request.inventory.platform,
            "floor_price": bid_request.inventory.floor_price
        }
    )
    
    try:
        # Get bid execution agent
        agent = get_bid_execution_agent()
        
        # Handle bid request
        response = await agent.handle_bid_request(bid_request)
        
        # Log response type
        if isinstance(response, BidResponse):
            logger.info(
                f"Bid submitted",
                extra={
                    "request_id": bid_request.request_id,
                    "bid_price": response.bid_price,
                    "campaign_id": response.campaign_id
                }
            )
        else:
            logger.info(
                f"No bid submitted",
                extra={
                    "request_id": bid_request.request_id,
                    "reason": response.reason
                }
            )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Error handling bid request",
            extra={
                "request_id": bid_request.request_id,
                "error": str(e)
            }
        )
        # Return no-bid on error to avoid timeout
        return NoBidResponse(
            request_id=bid_request.request_id,
            reason="Internal error"
        )


@router.post(
    "/bid-result",
    status_code=status.HTTP_200_OK,
    summary="Track bid result",
    description="Webhook endpoint for ad exchanges to notify of auction results (win/loss)"
)
async def track_bid_result(
    request_id: str,
    status: BidRequestStatus,
    win_price: float = None
) -> Dict[str, Any]:
    """
    Track bid result from ad exchange
    
    This endpoint receives notifications from ad exchanges about
    auction results (whether our bid won or lost).
    
    The agent uses this information to:
    - Track win rates
    - Adjust bidding strategy
    - Update campaign spend
    
    Args:
        request_id: Original bid request ID
        status: BID_WON or BID_LOST
        win_price: Actual price paid if won
        
    Returns:
        Success confirmation
        
    Requirements: 7.5
    """
    logger.info(
        f"Received bid result",
        extra={
            "request_id": request_id,
            "status": status,
            "win_price": win_price
        }
    )
    
    try:
        # Get bid execution agent
        agent = get_bid_execution_agent()
        
        # Track result
        await agent.track_bid_result(
            request_id=request_id,
            status=status,
            win_price=win_price
        )
        
        return {
            "success": True,
            "request_id": request_id,
            "status": status
        }
        
    except Exception as e:
        logger.error(
            f"Error tracking bid result",
            extra={
                "request_id": request_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking bid result: {str(e)}"
        )


@router.get(
    "/campaigns/{campaign_id}/bid-stats",
    status_code=status.HTTP_200_OK,
    summary="Get campaign bid statistics",
    description="Retrieve bidding statistics for a campaign"
)
async def get_campaign_bid_stats(
    campaign_id: str
) -> Dict[str, Any]:
    """
    Get bid statistics for a campaign
    
    Returns metrics including:
    - Total bids submitted
    - Win/loss counts
    - Win rate
    - Bid adjustment factor
    - Average bid prices
    
    Args:
        campaign_id: Campaign identifier
        
    Returns:
        Dictionary with bid statistics
    """
    logger.info(
        f"Getting bid stats for campaign",
        extra={"campaign_id": campaign_id}
    )
    
    try:
        # Get bid execution agent
        agent = get_bid_execution_agent()
        
        # Get stats
        stats = await agent.get_campaign_bid_stats(campaign_id)
        
        return stats
        
    except Exception as e:
        logger.error(
            f"Error getting bid stats",
            extra={
                "campaign_id": campaign_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting bid stats: {str(e)}"
        )


# Export router
bidding_router = router
