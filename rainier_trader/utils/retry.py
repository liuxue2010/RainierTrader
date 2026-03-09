import logging
import time
from typing import Callable, Any

logger = logging.getLogger(__name__)


def retry(fn: Callable, *args, retries: int = 3, base_delay: float = 1.0, **kwargs) -> Any:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1}/{retries} failed: {exc}. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError(f"All {retries} attempts failed") from last_exc
