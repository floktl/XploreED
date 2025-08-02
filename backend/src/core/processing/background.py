"""
XplorED - Background Processing Utilities

This module provides background processing and asynchronous task execution utilities,
following clean architecture principles as outlined in the documentation.

Background Processing Components:
- Asynchronous task execution
- Thread management
- Background job utilities

For detailed architecture information, see: docs/backend_structure.md
"""

import threading
from typing import Any, Callable
from shared.exceptions import TimeoutError


def run_in_background(func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """
    Execute a function asynchronously in a daemon thread.

    This utility allows for non-blocking execution of time-consuming operations
    such as AI processing, database updates, or external API calls.

    Args:
        func: Function to execute in background
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    """
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()


def run_with_timeout(func: Callable[..., Any], timeout: float, *args: Any, **kwargs: Any) -> Any:
    """
    Execute a function with a timeout.

    Args:
        func: Function to execute
        timeout: Timeout in seconds
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Any: Function result if completed within timeout

    Raises:
        TimeoutError: If function doesn't complete within timeout
    """
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError(f"Function {func.__name__} did not complete within {timeout} seconds")

    if exception[0]:
        raise exception[0]

    return result[0]


__all__ = [
    "run_in_background",
    "run_with_timeout",
]
