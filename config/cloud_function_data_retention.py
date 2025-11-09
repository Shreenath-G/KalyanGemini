"""
Cloud Function for scheduled data retention cleanup

This function should be deployed as a Cloud Function and triggered by Cloud Scheduler
to run daily data retention cleanup.

Deployment:
    gcloud functions deploy data-retention-cleanup \
        --runtime python311 \
        --trigger-topic data-retention-schedule \
        --entry-point scheduled_cleanup \
        --memory 512MB \
        --timeout 540s \
        --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id

Cloud Scheduler:
    gcloud scheduler jobs create pubsub data-retention-daily \
        --schedule="0 2 * * *" \
        --topic=data-retention-schedule \
        --message-body='{"retention_days": 90}' \
        --time-zone="America/New_York"
"""

import json
import logging
from typing import Dict, Any
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scheduled_cleanup(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Cloud Function entry point for scheduled data retention cleanup
    
    Args:
        event: Pub/Sub event data
        context: Cloud Function context
        
    Returns:
        Dictionary with cleanup results
    """
    logger.info("Starting scheduled data retention cleanup")
    
    try:
        # Parse event data
        if 'data' in event:
            import base64
            message_data = base64.b64decode(event['data']).decode('utf-8')
            config = json.loads(message_data)
        else:
            config = {}
        
        retention_days = config.get('retention_days', 90)
        dry_run = config.get('dry_run', False)
        
        logger.info(f"Cleanup configuration: retention_days={retention_days}, dry_run={dry_run}")
        
        # Import here to avoid issues with Cloud Function cold starts
        from src.services.data_retention import DataRetentionService
        
        # Run cleanup
        retention_service = DataRetentionService(retention_days=retention_days)
        results = asyncio.run(retention_service.run_full_cleanup(dry_run=dry_run))
        
        logger.info(f"Cleanup complete: {results}")
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e)
        }


def manual_cleanup(request) -> tuple:
    """
    HTTP Cloud Function entry point for manual data retention cleanup
    
    This allows administrators to trigger cleanup manually via HTTP request.
    
    Args:
        request: Flask request object
        
    Returns:
        Tuple of (response_body, status_code, headers)
    """
    logger.info("Manual data retention cleanup triggered")
    
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        if not request_json:
            request_json = {}
        
        retention_days = request_json.get('retention_days', 90)
        dry_run = request_json.get('dry_run', True)  # Default to dry run for safety
        
        # Verify authorization (in production, check admin credentials)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return (
                json.dumps({"error": "Unauthorized"}),
                401,
                {'Content-Type': 'application/json'}
            )
        
        logger.info(f"Manual cleanup: retention_days={retention_days}, dry_run={dry_run}")
        
        # Import and run cleanup
        from src.services.data_retention import DataRetentionService
        
        retention_service = DataRetentionService(retention_days=retention_days)
        results = asyncio.run(retention_service.run_full_cleanup(dry_run=dry_run))
        
        logger.info(f"Manual cleanup complete: {results}")
        
        return (
            json.dumps(results, default=str),
            200,
            {'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        logger.error(f"Manual cleanup failed: {e}", exc_info=True)
        return (
            json.dumps({"error": str(e)}),
            500,
            {'Content-Type': 'application/json'}
        )


def delete_account(request) -> tuple:
    """
    HTTP Cloud Function entry point for account deletion
    
    This allows account deletion to be triggered via HTTP request.
    
    Args:
        request: Flask request object
        
    Returns:
        Tuple of (response_body, status_code, headers)
    """
    logger.info("Account deletion triggered")
    
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        if not request_json:
            return (
                json.dumps({"error": "Missing request body"}),
                400,
                {'Content-Type': 'application/json'}
            )
        
        account_id = request_json.get('account_id')
        confirm = request_json.get('confirm', False)
        
        if not account_id:
            return (
                json.dumps({"error": "Missing account_id"}),
                400,
                {'Content-Type': 'application/json'}
            )
        
        if not confirm:
            return (
                json.dumps({"error": "Account deletion requires confirmation"}),
                400,
                {'Content-Type': 'application/json'}
            )
        
        # Verify authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return (
                json.dumps({"error": "Unauthorized"}),
                401,
                {'Content-Type': 'application/json'}
            )
        
        logger.warning(f"Deleting account: {account_id}")
        
        # Import and run deletion
        from src.services.data_retention import DataRetentionService
        
        retention_service = DataRetentionService()
        stats = asyncio.run(retention_service.delete_account_data(account_id))
        
        logger.info(f"Account deletion complete: {stats}")
        
        return (
            json.dumps({
                "status": "success",
                "account_id": account_id,
                "statistics": stats
            }),
            200,
            {'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        logger.error(f"Account deletion failed: {e}", exc_info=True)
        return (
            json.dumps({"error": str(e)}),
            500,
            {'Content-Type': 'application/json'}
        )
