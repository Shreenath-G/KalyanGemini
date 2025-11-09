"""API dependencies for dependency injection"""

from fastapi import Depends, Request
from typing import Optional

from src.api.auth import verify_api_key


async def get_account_id(
    request: Request,
    account_id: str = Depends(verify_api_key)
) -> str:
    """
    Get authenticated account ID from request
    
    This dependency can be used in route handlers to get the account ID
    """
    return account_id


def get_current_account_id(request: Request) -> Optional[str]:
    """
    Get account ID from request state (set by authentication middleware)
    
    Returns None if not authenticated
    """
    return getattr(request.state, "account_id", None)
