import time
import functools
from typing import Callable, Any, Optional
from utils.logger import logger

class Timer:
    """
    A class that can be used as a context manager or a decorator to measure
    execution times of functions, blocks, or pipelines.
    """
    def __init__(self, name: str = "Code Block", print_log: bool = True):
        self.name = name
        self.print_log = print_log
        self.start_time = 0.0
        self.elapsed = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start_time
        if self.print_log:
            logger.info(f"[Timer] '{self.name}' completed in {self.elapsed * 1000:.2f} ms")

    @staticmethod
    def decorator(name: Optional[str] = None, print_log: bool = True) -> Callable:
        """
        Decorator to measure function execution time.
        """
        def decorator_wrapper(func: Callable) -> Callable:
            timer_name = name or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                t = time.perf_counter()
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - t
                if print_log:
                    logger.info(f"[Timer] Function '{timer_name}' executed in {elapsed * 1000:.2f} ms")
                return result
            return wrapper
        return decorator_wrapper
