import time
import random
from config import MAX_RETRIES


def call_with_backoff(func, *args, **kwargs):
    """
    Calls the given function, automatically retrying with exponential backoff
    if it fails due to a transient server error (like a 503 'high demand' error).

    Usage: instead of calling client.models.generate_content(...) directly,
    wrap it: call_with_backoff(client.models.generate_content, model=..., contents=...)
    """
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_text = str(e)
            is_last_attempt = attempt == MAX_RETRIES - 1

            # Only retry on server-side/transient errors, not on bad input or auth errors
            is_transient = "503" in error_text or "UNAVAILABLE" in error_text or "429" in error_text

            if is_last_attempt or not is_transient:
                raise e

            sleep_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Transient error encountered, retrying in {sleep_time:.1f}s... (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(sleep_time)