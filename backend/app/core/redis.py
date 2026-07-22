import json
import time
import redis
from typing import Any, Optional
from app.core.config import settings

class RedisCache:
    def __init__(self):
        self._client = None
        self._last_fail_time = 0
        self._fallback_cache = {}  # Local in-memory fallback: key -> value
        self._fallback_expiry = {}  # Local in-memory fallback: key -> timestamp

    @property
    def client(self):
        if self._client is not None:
            return self._client
        
        # Avoid blocking socket timeouts on every request if Redis is down (60s cooldown)
        if time.time() - self._last_fail_time < 60:
            return None

        try:
            # Initialize redis connection with strict sub-second timeouts (500ms)
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5
            )
            self._client.ping()
            print("Redis successfully connected!")
        except Exception as e:
            self._last_fail_time = time.time()
            self._client = None
        return self._client

    def get(self, key: str) -> Optional[Any]:
        client = self.client
        if client:
            try:
                val = client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                self._last_fail_time = time.time()
                self._client = None
        
        # Fast local in-memory fallback
        if key in self._fallback_cache:
            expiry = self._fallback_expiry.get(key)
            if expiry is None or expiry > time.time():
                return self._fallback_cache[key]
            else:
                self._fallback_cache.pop(key, None)
                self._fallback_expiry.pop(key, None)
        return None

    def set(self, key: str, value: Any, ex: int = None) -> bool:
        client = self.client
        if client:
            try:
                client.set(key, json.dumps(value), ex=ex)
                return True
            except Exception as e:
                self._last_fail_time = time.time()
                self._client = None
        
        # Fast local in-memory fallback
        self._fallback_cache[key] = value
        if ex:
            self._fallback_expiry[key] = time.time() + ex
        else:
            self._fallback_expiry[key] = None
        return True

    def delete(self, key: str) -> bool:
        client = self.client
        if client:
            try:
                client.delete(key)
                return True
            except Exception as e:
                self._last_fail_time = time.time()
                self._client = None
        
        self._fallback_cache.pop(key, None)
        self._fallback_expiry.pop(key, None)
        return True

    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching the pattern."""
        client = self.client
        count = 0
        if client:
            try:
                keys = list(client.scan_iter(match=pattern))
                if keys:
                    count = client.delete(*keys)
                return count
            except Exception as e:
                self._last_fail_time = time.time()
                self._client = None
        
        import fnmatch
        keys_to_remove = [k for k in self._fallback_cache.keys() if fnmatch.fnmatch(str(k), pattern)]
        for k in keys_to_remove:
            self._fallback_cache.pop(k, None)
            self._fallback_expiry.pop(k, None)
            count += 1
        return count

redis_cache = RedisCache()
