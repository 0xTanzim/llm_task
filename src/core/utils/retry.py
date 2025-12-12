"""Retry utilities with exponential backoff for robust API calls."""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator for retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        retry_on: Tuple of exception types to retry on (default: all exceptions)

    Example:
        @retry_with_exponential_backoff(max_retries=3, initial_delay=1.0)
        def call_api():
            return requests.get("https://api.example.com/data")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt == max_retries:
                        print(
                            f"❌ Max retries ({max_retries}) reached for {func.__name__}"
                        )
                        raise

                    # Calculate next delay with exponential backoff
                    current_delay = min(delay, max_delay)
                    print(
                        f"⚠️ Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {current_delay:.1f}s: {e}"
                    )
                    time.sleep(current_delay)
                    delay *= backoff_factor

            # This should never be reached, but for type safety
            if last_exception:
                raise last_exception
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt == max_retries:
                        print(
                            f"❌ Max retries ({max_retries}) reached for {func.__name__}"
                        )
                        raise

                    # Calculate next delay with exponential backoff
                    current_delay = min(delay, max_delay)
                    print(
                        f"⚠️ Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {current_delay:.1f}s: {e}"
                    )
                    await asyncio.sleep(current_delay)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception
            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def create_retry_config(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
) -> dict[str, Any]:
    """
    Create a retry configuration for LangChain RunnableConfig.

    This can be passed to model invocations via the config parameter.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry

    Returns:
        Configuration dict for LangChain models

    Example:
        config = create_retry_config(max_retries=3)
        response = model.invoke(messages, config=config)
    """
    return {
        "max_retries": max_retries,
        "retry_delay": initial_delay,
        "retry_backoff_factor": backoff_factor,
    }
