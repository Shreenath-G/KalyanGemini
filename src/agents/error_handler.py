"""Error handling and fallback strategies for agents"""

import logging
import asyncio
from typing import Dict, Any, Callable, Optional, TypeVar, ParamSpec
from functools import wraps
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

# Type variables for generic decorator
P = ParamSpec('P')
T = TypeVar('T')


class AgentErrorHandler:
    """
    Error handler for agent failures with fallback strategies
    
    Provides fallback strategies for each specialist agent:
    - Creative Generator: Template-based generation
    - Audience Targeting: Broad category targeting
    - Budget Optimizer: Equal distribution
    
    Requirements: 12.2, 12.3
    """
    
    @staticmethod
    def get_fallback_strategy(agent_name: str) -> Callable:
        """
        Get fallback strategy for a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Fallback function for the agent
        """
        fallback_strategies = {
            "creative_generator": AgentErrorHandler._creative_fallback,
            "audience_targeting": AgentErrorHandler._audience_fallback,
            "budget_optimizer": AgentErrorHandler._budget_fallback
        }
        
        return fallback_strategies.get(
            agent_name,
            AgentErrorHandler._default_fallback
        )
    
    @staticmethod
    def _creative_fallback(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback strategy for Creative Generator Agent
        
        Uses template-based creative generation
        
        Args:
            campaign_data: Campaign information
            
        Returns:
            Dictionary with fallback creative variants
        """
        logger.warning("Using template-based creative generation (fallback)")
        
        product = campaign_data.get("products", ["our product"])[0]
        goal = campaign_data.get("business_goal", "grow your business").replace("_", " ").title()
        
        variations = [
            {
                "variant_id": f"var_{campaign_data.get('campaign_id', 'unknown')}_{i}",
                "headlines": {
                    "short": f"{goal} Now",
                    "medium": f"{goal} with {product}",
                    "long": f"Achieve {goal} with {product} - Get Started Today"
                },
                "body": f"Transform your business with {product}. Easy setup, powerful results.",
                "cta": "Get Started",
                "compliance_score": 0.85,
                "fallback": True
            }
            for i in range(3)
        ]
        
        return {"variations": variations}
    
    @staticmethod
    def _audience_fallback(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback strategy for Audience Targeting Agent
        
        Uses broad category targeting
        
        Args:
            campaign_data: Campaign information
            
        Returns:
            Dictionary with fallback audience segments
        """
        logger.warning("Using broad category targeting (fallback)")
        
        segments = [
            {
                "segment_id": f"seg_{campaign_data.get('campaign_id', 'unknown')}_broad",
                "name": "Broad Target Audience",
                "demographics": {
                    "age_range": "25-65",
                    "gender": "all",
                    "income": "all"
                },
                "interests": ["business", "technology"],
                "behaviors": ["online shopping"],
                "estimated_size": "large",
                "conversion_probability": 0.05,
                "priority_score": 0.5,
                "fallback": True
            }
        ]
        
        return {"segments": segments}
    
    @staticmethod
    def _budget_fallback(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback strategy for Budget Optimizer Agent
        
        Uses equal distribution across segments
        
        Args:
            campaign_data: Campaign information
            
        Returns:
            Dictionary with fallback budget allocation
        """
        logger.warning("Using equal distribution budget allocation (fallback)")
        
        monthly_budget = campaign_data.get("monthly_budget", 1000.0)
        daily_budget = monthly_budget / 30
        
        allocation = {
            "campaign_id": campaign_data.get("campaign_id"),
            "total_budget": monthly_budget,
            "daily_budget": daily_budget,
            "test_budget": monthly_budget * 0.20,
            "allocations": [
                {
                    "segment_id": "default",
                    "daily_budget": daily_budget,
                    "platform_split": {
                        "google_ads": daily_budget * 0.40,
                        "meta_ads": daily_budget * 0.40,
                        "programmatic": daily_budget * 0.20
                    },
                    "max_cpc": 2.00
                }
            ],
            "fallback": True
        }
        
        return {"allocation": allocation}
    
    @staticmethod
    def _default_fallback(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default fallback strategy for unknown agents
        
        Args:
            campaign_data: Campaign information
            
        Returns:
            Empty dictionary
        """
        logger.warning("Using default fallback (no specific strategy)")
        return {}
    
    @staticmethod
    def handle_agent_error(
        agent_name: str,
        error: Exception,
        campaign_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle agent error and apply fallback strategy
        
        This method:
        1. Logs error with full context and stack trace
        2. Applies agent-specific fallback strategy
        3. Sends alert for monitoring
        4. Returns fallback result with error metadata
        
        Args:
            agent_name: Name of the failed agent
            error: Exception that occurred
            campaign_data: Campaign information for fallback
            
        Returns:
            Fallback result with error metadata
            
        Requirements: 12.2, 12.3
        """
        # Log error with full context
        logger.error(
            f"Agent {agent_name} failed - applying fallback strategy",
            extra={
                "agent": agent_name,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc(),
                "campaign_id": campaign_data.get("campaign_id") if campaign_data else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Send alert for monitoring
        AgentErrorHandler._send_alert(agent_name, error, campaign_data)
        
        # Get and execute fallback strategy
        fallback = AgentErrorHandler.get_fallback_strategy(agent_name)
        
        try:
            if campaign_data:
                result = fallback(campaign_data)
            else:
                result = {}
            
            logger.info(
                f"Fallback strategy applied successfully for {agent_name}",
                extra={
                    "agent": agent_name,
                    "fallback_result_keys": list(result.keys())
                }
            )
        except Exception as fallback_error:
            logger.critical(
                f"Fallback strategy failed for {agent_name}",
                extra={
                    "agent": agent_name,
                    "original_error": str(error),
                    "fallback_error": str(fallback_error),
                    "stack_trace": traceback.format_exc()
                }
            )
            result = {}
        
        # Add error metadata
        result["error"] = str(error)
        result["error_type"] = type(error).__name__
        result["fallback_applied"] = True
        result["agent_name"] = agent_name
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result
    
    @staticmethod
    def _send_alert(
        agent_name: str,
        error: Exception,
        campaign_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send alert for agent failure
        
        In production, this would integrate with:
        - Cloud Monitoring for alerting
        - PagerDuty or similar for on-call notifications
        - Slack/email for team notifications
        
        For now, logs a critical alert that monitoring systems can pick up.
        
        Args:
            agent_name: Name of the failed agent
            error: Exception that occurred
            campaign_data: Campaign context
        """
        alert_data = {
            "alert_type": "agent_failure",
            "severity": "high",
            "agent": agent_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "campaign_id": campaign_data.get("campaign_id") if campaign_data else None,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_investigation": True
        }
        
        # Log as critical for monitoring systems to pick up
        logger.critical(
            f"ALERT: Agent failure detected - {agent_name}",
            extra=alert_data
        )
        
        # TODO: Integrate with actual alerting systems
        # - Cloud Monitoring alert policies
        # - PagerDuty incident creation
        # - Slack webhook notification
        # - Email notification to ops team


def with_timeout_and_retry(
    timeout: int = 30,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    retry_on: Optional[tuple] = None
):
    """
    Decorator for agent methods with timeout and retry logic
    
    This decorator provides:
    1. Timeout enforcement using asyncio.wait_for
    2. Automatic retry with exponential backoff
    3. Configurable retry conditions
    4. Detailed logging of attempts and failures
    5. Graceful degradation on timeout or max retries
    
    Args:
        timeout: Timeout in seconds for each attempt
        max_retries: Maximum number of retry attempts
        backoff_base: Base for exponential backoff (default: 2.0)
        retry_on: Tuple of exception types to retry on (None = retry on all)
        
    Returns:
        Decorated async function with timeout and retry logic
        
    Requirements: 2.4, 12.3
    
    Example:
        @with_timeout_and_retry(timeout=30, max_retries=3)
        async def my_agent_method(self, data):
            # Method implementation
            pass
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Optional[Exception] = None
            function_name = func.__name__
            
            # Extract agent name from args if available (self.name)
            agent_name = "unknown"
            if args and hasattr(args[0], 'name'):
                agent_name = args[0].name
            
            for attempt in range(max_retries):
                attempt_num = attempt + 1
                
                try:
                    logger.debug(
                        f"Executing {function_name} (attempt {attempt_num}/{max_retries})",
                        extra={
                            "function": function_name,
                            "agent": agent_name,
                            "attempt": attempt_num,
                            "max_retries": max_retries,
                            "timeout": timeout
                        }
                    )
                    
                    # Execute function with timeout
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                    
                    # Success - log if this wasn't the first attempt
                    if attempt > 0:
                        logger.info(
                            f"{function_name} succeeded after {attempt_num} attempts",
                            extra={
                                "function": function_name,
                                "agent": agent_name,
                                "attempts": attempt_num
                            }
                        )
                    
                    return result
                    
                except asyncio.TimeoutError as e:
                    last_error = e
                    logger.warning(
                        f"{function_name} timed out after {timeout}s (attempt {attempt_num}/{max_retries})",
                        extra={
                            "function": function_name,
                            "agent": agent_name,
                            "attempt": attempt_num,
                            "max_retries": max_retries,
                            "timeout": timeout,
                            "error_type": "TimeoutError"
                        }
                    )
                    
                except Exception as e:
                    last_error = e
                    
                    # Check if we should retry this exception type
                    should_retry = True
                    if retry_on is not None:
                        should_retry = isinstance(e, retry_on)
                    
                    if not should_retry:
                        logger.error(
                            f"{function_name} failed with non-retryable error",
                            extra={
                                "function": function_name,
                                "agent": agent_name,
                                "error_type": type(e).__name__,
                                "error": str(e),
                                "stack_trace": traceback.format_exc()
                            }
                        )
                        raise
                    
                    logger.warning(
                        f"{function_name} failed (attempt {attempt_num}/{max_retries})",
                        extra={
                            "function": function_name,
                            "agent": agent_name,
                            "attempt": attempt_num,
                            "max_retries": max_retries,
                            "error_type": type(e).__name__,
                            "error": str(e)
                        }
                    )
                
                # Apply exponential backoff before next retry
                if attempt < max_retries - 1:
                    backoff_time = backoff_base ** attempt
                    logger.debug(
                        f"Waiting {backoff_time}s before retry",
                        extra={
                            "function": function_name,
                            "agent": agent_name,
                            "backoff_time": backoff_time,
                            "next_attempt": attempt_num + 1
                        }
                    )
                    await asyncio.sleep(backoff_time)
            
            # All retries exhausted
            logger.error(
                f"{function_name} failed after {max_retries} attempts",
                extra={
                    "function": function_name,
                    "agent": agent_name,
                    "max_retries": max_retries,
                    "final_error_type": type(last_error).__name__ if last_error else "Unknown",
                    "final_error": str(last_error) if last_error else "Unknown",
                    "stack_trace": traceback.format_exc() if last_error else None
                }
            )
            
            # Raise the last error
            if last_error:
                raise last_error
            else:
                raise RuntimeError(f"{function_name} failed after {max_retries} attempts")
        
        return wrapper
    return decorator


def with_graceful_degradation(
    fallback_value: Any = None,
    log_level: str = "error"
):
    """
    Decorator that ensures graceful degradation when agents are unavailable
    
    Instead of raising exceptions, returns a fallback value and logs the error.
    Useful for non-critical agent operations where system should continue.
    
    Args:
        fallback_value: Value to return on error (default: None)
        log_level: Logging level for errors ("error", "warning", "info")
        
    Returns:
        Decorated function that returns fallback_value on error
        
    Requirements: 12.3
    
    Example:
        @with_graceful_degradation(fallback_value=[])
        async def get_optional_data(self):
            # Method that can fail without breaking the system
            pass
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            function_name = func.__name__
            
            # Extract agent name from args if available
            agent_name = "unknown"
            if args and hasattr(args[0], 'name'):
                agent_name = args[0].name
            
            try:
                return await func(*args, **kwargs)
                
            except Exception as e:
                # Log at specified level
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"{function_name} failed - using graceful degradation",
                    extra={
                        "function": function_name,
                        "agent": agent_name,
                        "error_type": type(e).__name__,
                        "error": str(e),
                        "fallback_value": str(fallback_value),
                        "stack_trace": traceback.format_exc()
                    }
                )
                
                return fallback_value
        
        return wrapper
    return decorator



class AgentCommunicationError(Exception):
    """Exception raised when agent-to-agent communication fails"""
    
    def __init__(
        self,
        agent_name: str,
        message: str,
        original_error: Optional[Exception] = None
    ):
        self.agent_name = agent_name
        self.original_error = original_error
        super().__init__(f"Agent {agent_name} communication failed: {message}")


class AgentTimeoutError(Exception):
    """Exception raised when agent operation times out"""
    
    def __init__(
        self,
        agent_name: str,
        timeout: int,
        operation: str
    ):
        self.agent_name = agent_name
        self.timeout = timeout
        self.operation = operation
        super().__init__(
            f"Agent {agent_name} operation '{operation}' timed out after {timeout}s"
        )


def handle_agent_communication_error(
    source_agent: str,
    target_agent: str,
    error: Exception,
    campaign_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Handle errors in agent-to-agent communication
    
    This function:
    1. Logs the communication failure
    2. Applies fallback strategy for the target agent
    3. Returns fallback result that allows workflow to continue
    
    Args:
        source_agent: Name of the agent initiating communication
        target_agent: Name of the agent that failed to respond
        error: Exception that occurred
        campaign_data: Campaign context for fallback
        
    Returns:
        Fallback result from target agent's fallback strategy
        
    Requirements: 12.2, 12.3
    """
    logger.error(
        f"Agent communication failed: {source_agent} -> {target_agent}",
        extra={
            "source_agent": source_agent,
            "target_agent": target_agent,
            "error_type": type(error).__name__,
            "error": str(error),
            "campaign_id": campaign_data.get("campaign_id") if campaign_data else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    # Use the target agent's fallback strategy
    return AgentErrorHandler.handle_agent_error(
        agent_name=target_agent,
        error=error,
        campaign_data=campaign_data
    )


async def execute_with_fallback(
    agent_func: Callable,
    agent_name: str,
    campaign_data: Dict[str, Any],
    timeout: int = 30,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Execute an agent function with automatic fallback on failure
    
    This is a convenience function that combines:
    - Timeout enforcement
    - Retry logic with exponential backoff
    - Automatic fallback strategy application
    - Comprehensive error logging
    
    Args:
        agent_func: Async function to execute
        agent_name: Name of the agent for fallback strategy
        campaign_data: Campaign context
        timeout: Timeout in seconds per attempt
        max_retries: Maximum retry attempts
        
    Returns:
        Result from agent function or fallback strategy
        
    Requirements: 2.4, 12.2, 12.3
    """
    last_error: Optional[Exception] = None
    
    for attempt in range(max_retries):
        try:
            logger.debug(
                f"Executing {agent_name} function (attempt {attempt + 1}/{max_retries})",
                extra={
                    "agent": agent_name,
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "timeout": timeout
                }
            )
            
            # Execute with timeout
            result = await asyncio.wait_for(agent_func(), timeout=timeout)
            
            # Success
            if attempt > 0:
                logger.info(
                    f"{agent_name} succeeded after {attempt + 1} attempts",
                    extra={"agent": agent_name, "attempts": attempt + 1}
                )
            
            return result
            
        except asyncio.TimeoutError as e:
            last_error = AgentTimeoutError(agent_name, timeout, "function_execution")
            logger.warning(
                f"{agent_name} timed out (attempt {attempt + 1}/{max_retries})",
                extra={
                    "agent": agent_name,
                    "attempt": attempt + 1,
                    "timeout": timeout
                }
            )
            
        except Exception as e:
            last_error = e
            logger.warning(
                f"{agent_name} failed (attempt {attempt + 1}/{max_retries})",
                extra={
                    "agent": agent_name,
                    "attempt": attempt + 1,
                    "error_type": type(e).__name__,
                    "error": str(e)
                }
            )
        
        # Exponential backoff before retry
        if attempt < max_retries - 1:
            backoff_time = 2 ** attempt
            await asyncio.sleep(backoff_time)
    
    # All retries failed - apply fallback
    logger.error(
        f"{agent_name} failed after {max_retries} attempts - applying fallback",
        extra={
            "agent": agent_name,
            "max_retries": max_retries,
            "final_error": str(last_error)
        }
    )
    
    return AgentErrorHandler.handle_agent_error(
        agent_name=agent_name,
        error=last_error,
        campaign_data=campaign_data
    )
