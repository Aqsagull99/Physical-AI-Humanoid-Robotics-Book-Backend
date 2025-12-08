import time
import functools
from typing import Callable, Any
from core.logging import logger


def monitor_performance(func: Callable) -> Callable:
    """
    Decorator to monitor the performance of functions
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log performance metrics
            logger.info(f"Performance: {func.__name__} executed in {execution_time:.4f}s")

            # Log warning if execution time exceeds threshold (1 second)
            if execution_time > 1.0:
                logger.warning(f"Performance: {func.__name__} took {execution_time:.4f}s (slow execution)")

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Performance: {func.__name__} failed after {execution_time:.4f}s with error: {str(e)}")
            raise

    return wrapper


def time_function(func: Callable) -> Callable:
    """
    Decorator to time function execution
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"Function {func.__name__} took {execution_time:.4f}s")
        return result

    return wrapper


class PerformanceMonitor:
    """
    Performance monitoring class to track various metrics
    """
    def __init__(self):
        self.metrics = {}

    def start_timer(self, name: str):
        """Start a timer with the given name"""
        self.metrics[name] = time.time()

    def stop_timer(self, name: str) -> float:
        """Stop the timer and return the elapsed time"""
        if name in self.metrics:
            elapsed = time.time() - self.metrics[name]
            logger.info(f"Performance: {name} took {elapsed:.4f}s")
            del self.metrics[name]
            return elapsed
        else:
            logger.warning(f"Performance: Timer {name} not found")
            return 0.0


# Global performance monitor instance
perf_monitor = PerformanceMonitor()