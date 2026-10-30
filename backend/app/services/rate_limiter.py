import math
import threading
import time
from collections import deque


class RateLimiter:
    """Sliding-window limiter, in memory (one server process).

    rules: list of (window_seconds, max_requests). Every rule must pass.
    """

    def __init__(self, rules, max_keys: int = 10_000):
        self.rules = rules
        self.max_keys = max_keys
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def check(self, key: str, now: float | None = None) -> int:
        """Return 0 and record the hit if allowed, else seconds to wait."""
        now = time.monotonic() if now is None else now
        longest = max(window for window, _ in self.rules)

        with self._lock:
            if len(self._hits) > self.max_keys:
                self._prune(now, longest)

            hits = self._hits.setdefault(key, deque())

            while hits and now - hits[0] >= longest:
                hits.popleft()

            for window, limit in self.rules:
                recent = [t for t in hits if now - t < window]
                if len(recent) >= limit:
                    return max(1, math.ceil(window - (now - recent[0])))

            hits.append(now)
            return 0

    def _prune(self, now: float, longest: float) -> None:
        for key in [
            k for k, hits in self._hits.items()
            if not hits or now - hits[-1] >= longest
        ]:
            del self._hits[key]