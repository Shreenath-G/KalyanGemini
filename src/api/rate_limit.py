"""Rate limiting implementation"""

from fastapi import Request
from typing import Dict, Tuple
import time
import logging
from collections import defaultdict
from threading import Lock

from src.config import settings
from src.api.errors import RateLimitError

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter
    
    Tracks requests per account per minute
    In production, this should use Redis or Memorystore for distributed rate limiting
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def _clean_old_requests(self, account_id: str, current_time: float) -> None:
        """Remove requests outside the current time window"""
        cutoff_time = current_time - self.window_seconds
        self.requests[account_id] = [
            req_time for req_time in self.requests[account_id]
            if req_time > cutoff_time
        ]
    
    def check_rate_limit(self, account_id: str) -> Tuple[bool, int]:
        """
        Check if request is within rate limit
        
        Args:
            account_id: Account identifier
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        with self.lock:
            current_time = time.time()
            
            # Clean old requests
            self._clean_old_requests(account_id, current_time)
            
            # Check if under limit
            request_count = len(self.requests[account_id])
            
            if request_count >= self.max_requests:
                # Calculate retry_after based on oldest request in window
                oldest_request = min(self.requests[account_id])
                retry_after = int(oldest_request + self.window_seconds - current_time) + 1
                
                logger.warning(
                    f"Rate limit exceeded for account {account_id}: "
                    f"{request_count}/{self.max_requests} requests"
                )
                
                return False, retry_after
            
            # Add current request
            self.requests[account_id].append(current_time)
            
            return True, 0
    
    def get_remaining_requests(self, account_id: str) -> int:
        """Get number of remaining requests in current window"""
        with self.lock:
            current_time = time.time()
            self._clean_old_requests(account_id, current_time)
            request_count = len(self.requests[account_id])
            return max(0, self.max_requests - request_count)
    
    def reset_account(self, account_id: str) -> None:
        """Reset rate limit for an account (for testing)"""
        with self.lock:
            if account_id in self.requests:
                del self.requests[account_id]


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)


async def check_rate_limit(request: Request, account_id: str) -> None:
    """
    Check rate limit for the current request
    
    Args:
        request: FastAPI request object
        account_id: Account identifier
        
    Raises:
        RateLimitError: If rate limit is exceeded
    """
    is_allowed, retry_after = rate_limiter.check_rate_limit(account_id)
    
    if not is_allowed:
        logger.warning(
            f"Rate limit exceeded",
            extra={
                "account_id": account_id,
                "path": request.url.path,
                "retry_after": retry_after
            }
        )
        raise RateLimitError(retry_after=retry_after)
    
    # Add rate limit info to response headers (will be added by middleware)
    remaining = rate_limiter.get_remaining_requests(account_id)
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = settings.rate_limit_per_minute
