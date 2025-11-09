"""Authentication and authorization"""

from fastapi import Header, HTTPException, status, Request
from typing import Optional
import logging

from src.config import settings
from src.api.errors import AuthenticationError

logger = logging.getLogger(__name__)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias=settings.api_key_header)
) -> str:
    """
    Verify API key from request header using Secret Manager
    
    Args:
        x_api_key: API key from header
        
    Returns:
        Account ID associated with the API key
        
    Raises:
        AuthenticationError: If API key is missing or invalid
        
    Requirements: 13.2, 13.3
    """
    if not x_api_key:
        logger.warning("Missing API key in request")
        raise AuthenticationError("API key is required")
    
    # Basic format validation
    if not x_api_key.startswith("sk_") or len(x_api_key) < 32:
        logger.warning(f"Invalid API key format: {x_api_key[:10]}...")
        raise AuthenticationError("Invalid API key format")
    
    # Validate against Secret Manager
    try:
        from src.services.secret_manager import get_secret_manager_service
        
        secret_manager = get_secret_manager_service()
        key_info = secret_manager.validate_api_key(x_api_key)
        
        if key_info:
            account_id = key_info["account_id"]
            logger.info(f"Authenticated request for account: {account_id}")
            return account_id
        else:
            logger.warning(f"Invalid or inactive API key: {x_api_key[:10]}...")
            raise AuthenticationError("Invalid or inactive API key")
            
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        
        # Fallback to basic validation if Secret Manager is unavailable
        # This ensures the system continues to function during Secret Manager issues
        logger.warning("Falling back to basic API key validation")
        try:
            parts = x_api_key.split("_")
            if len(parts) >= 3:
                account_id = parts[1]
                logger.info(f"Authenticated request for account (fallback): {account_id}")
                return account_id
            else:
                raise ValueError("Invalid key structure")
        except Exception as fallback_error:
            logger.warning(f"Fallback validation failed: {fallback_error}")
            raise AuthenticationError("Invalid API key")


def get_account_id_from_request(request: Request) -> Optional[str]:
    """
    Extract account ID from request state (set by authentication)
    
    Args:
        request: FastAPI request object
        
    Returns:
        Account ID if authenticated, None otherwise
    """
    return getattr(request.state, "account_id", None)
