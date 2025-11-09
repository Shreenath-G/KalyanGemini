"""Data export API routes for GDPR compliance"""

from fastapi import APIRouter, Depends, Request, Query, Response
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import logging
from datetime import datetime
import io

from src.api.dependencies import get_current_account_id
from src.api.errors import NotFoundError, ValidationError
from src.services.data_export import get_data_export_service
from src.services.data_retention import DataRetentionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data", tags=["Data Management"])


@router.get(
    "/export",
    summary="Export account data",
    description="""Export all data for the authenticated account (GDPR compliance).
    
    **Data Included:**
    - All campaigns (configuration and status)
    - Creative variants (headlines, body copy, CTAs)
    - Audience segments (targeting criteria)
    - Budget allocations (spend distribution)
    - Performance metrics (optional)
    
    **Export Formats:**
    - `json`: Structured JSON format (default)
    - `csv`: Comma-separated values
    
    **Use Cases:**
    - GDPR data portability requests
    - Backup and archival
    - External analysis and reporting
    
    **Authentication Required:** API Key in X-API-Key header
    """,
    responses={
        200: {
            "description": "Data exported successfully",
            "content": {
                "application/json": {
                    "example": {
                        "account_id": "acc_123456",
                        "export_date": "2025-11-09T10:30:00Z",
                        "campaigns": [
                            {
                                "campaign_id": "camp_a1b2c3d4e5f6",
                                "status": "active",
                                "business_goal": "increase_sales",
                                "monthly_budget": 5000.0,
                                "created_at": "2025-11-01T08:00:00Z"
                            }
                        ],
                        "total_campaigns": 1,
                        "total_spend": 1250.50
                    }
                }
            }
        },
        400: {
            "description": "Validation error"
        },
        401: {
            "description": "Authentication failed"
        }
    }
)
async def export_account_data(
    request: Request,
    format: str = Query("json", regex="^(json|csv)$"),
    include_metrics: bool = Query(True, description="Include performance metrics in export")
) -> Response:
    """
    Export all data for an account
    
    This endpoint exports:
    - All campaigns
    - Creative variants
    - Audience segments
    - Budget allocations
    - Performance metrics (optional)
    
    Requirements: 13.5, 14.1, 14.2, 14.3
    """
    account_id = get_current_account_id(request)
    
    if not account_id:
        raise ValidationError("Account ID not found in request")
    
    logger.info(f"Exporting data for account: {account_id} (format: {format})")
    
    try:
        export_service = get_data_export_service()
        
        # Export data
        export_data = await export_service.export_account_data(
            account_id=account_id,
            format=format,
            include_metrics=include_metrics
        )
        
        # Format response based on requested format
        if format == "json":
            content = export_service.format_as_json(export_data, pretty=True)
            media_type = "application/json"
            filename = f"account_{account_id}_export_{datetime.now().strftime('%Y%m%d')}.json"
        else:  # csv
            content = export_service.format_as_csv(export_data)
            media_type = "text/csv"
            filename = f"account_{account_id}_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Return as downloadable file
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting data for account {account_id}: {e}")
        raise


@router.get(
    "/export/campaign/{campaign_id}",
    summary="Export campaign data",
    description="Export data for a specific campaign"
)
async def export_campaign_data(
    campaign_id: str,
    request: Request,
    format: str = Query("json", regex="^(json|csv)$")
) -> Response:
    """
    Export data for a specific campaign
    
    Requirements: 13.5
    """
    account_id = get_current_account_id(request)
    
    if not account_id:
        raise ValidationError("Account ID not found in request")
    
    logger.info(f"Exporting campaign: {campaign_id} for account: {account_id}")
    
    try:
        export_service = get_data_export_service()
        
        # Export campaign data
        export_data = await export_service.export_campaign_data(
            campaign_id=campaign_id,
            account_id=account_id,
            format=format
        )
        
        # Format response
        if format == "json":
            content = export_service.format_as_json(export_data, pretty=True)
            media_type = "application/json"
            filename = f"campaign_{campaign_id}_export_{datetime.now().strftime('%Y%m%d')}.json"
        else:  # csv
            content = export_service.format_as_csv(export_data)
            media_type = "text/csv"
            filename = f"campaign_{campaign_id}_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ValueError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        logger.error(f"Error exporting campaign {campaign_id}: {e}")
        raise


@router.get(
    "/export/performance-report",
    summary="Export performance report",
    description="Export performance report for all campaigns"
)
async def export_performance_report(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)")
) -> JSONResponse:
    """
    Export performance report for an account
    
    Requirements: 8.1, 13.5
    """
    account_id = get_current_account_id(request)
    
    if not account_id:
        raise ValidationError("Account ID not found in request")
    
    logger.info(f"Generating performance report for account: {account_id}")
    
    try:
        export_service = get_data_export_service()
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Generate report
        report = await export_service.export_performance_report(
            account_id=account_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return JSONResponse(content=report)
        
    except ValueError as e:
        raise ValidationError(f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error generating performance report for {account_id}: {e}")
        raise


@router.delete(
    "/account",
    summary="Delete account data",
    description="Delete all data for the authenticated account (account closure)"
)
async def delete_account_data(
    request: Request,
    confirm: bool = Query(False, description="Confirmation flag (must be true)")
) -> JSONResponse:
    """
    Delete all data for an account (account closure)
    
    This is a destructive operation that cannot be undone.
    All campaigns, metrics, and related data will be permanently deleted.
    
    Requirements: 13.5
    """
    account_id = get_current_account_id(request)
    
    if not account_id:
        raise ValidationError("Account ID not found in request")
    
    if not confirm:
        raise ValidationError("Account deletion requires confirmation (confirm=true)")
    
    logger.warning(f"Deleting all data for account: {account_id}")
    
    try:
        retention_service = DataRetentionService()
        
        # Delete all account data
        stats = await retention_service.delete_account_data(account_id)
        
        logger.info(f"Account data deleted: {stats}")
        
        return JSONResponse(
            content={
                "message": "Account data successfully deleted",
                "account_id": account_id,
                "deleted_at": datetime.now().isoformat(),
                "statistics": stats
            }
        )
        
    except Exception as e:
        logger.error(f"Error deleting account data for {account_id}: {e}")
        raise
