import time
import functools
import logging

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        logging.info(f"{func.__name__} took {elapsed_time:.2f} seconds to complete.")
        return result
    return wrapper


