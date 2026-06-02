"""Redis adapter — stub (Redis is optional in offline deployment)."""
import logging

logger = logging.getLogger(__name__)


class RedisAdapter:
    """No-op Redis adapter for offline/single-machine deployments."""

    def __init__(self):
        self._data = {}

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value, ttl: int = None):
        self._data[key] = value
        return True

    def delete(self, key: str):
        self._data.pop(key, None)
        return True

    def exists(self, key: str) -> bool:
        return key in self._data

    def flush(self):
        self._data.clear()


redis_adapter = RedisAdapter()
