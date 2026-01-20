"""
Danbooru API Plugin - HTTP helpers
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import asyncio
import json


@dataclass
class RequestOptions:
    """请求选项"""
    timeout: Optional[int] = None
    retries: Optional[int] = None
    use_auth: bool = True
    auth_method: str = "header"  # "header" or "params"
    response_format: str = "json"  # "json" or "xml"


class RateLimiter:
    """速率限制器"""

    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self._last_request_time: float = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """获取请求许可"""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time

            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                await asyncio.sleep(wait_time)

            self._last_request_time = asyncio.get_event_loop().time()

    def update_rate(self, new_rate: int) -> None:
        """更新速率限制"""
        self.requests_per_second = new_rate
        self.min_interval = 1.0 / new_rate


class ResponseCache:
    """响应缓存"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, tuple] = {}  # key -> (value, expires_at)
        self._lock = asyncio.Lock()

    def _generate_key(self, method: str, url: str, params: Optional[Dict] = None) -> str:
        """生成缓存键"""
        key_parts = [method.upper(), url]
        if params:
            sorted_params = sorted(params.items())
            key_parts.append(str(sorted_params))
        return ":".join(key_parts)

    async def get(self, method: str, url: str, params: Optional[Dict] = None) -> Optional[Any]:
        """获取缓存"""
        key = self._generate_key(method, url, params)
        async with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if datetime.now() < expires_at:
                    return value
                del self._cache[key]
        return None

    async def set(
        self,
        method: str,
        url: str,
        value: Any,
        params: Optional[Dict] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """设置缓存"""
        key = self._generate_key(method, url, params)
        expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)

        async with self._lock:
            if len(self._cache) >= self.max_size:
                await self._cleanup()
            self._cache[key] = (value, expires_at)

    async def _cleanup(self) -> None:
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expires_at) in self._cache.items()
            if now >= expires_at
        ]
        for key in expired_keys:
            del self._cache[key]

        if len(self._cache) >= self.max_size:
            sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])
            for key, _ in sorted_items[:len(self._cache) - self.max_size + 1]:
                del self._cache[key]

    def _estimate_entry_size(self, key: str, value: Any) -> int:
        """估算缓存条目占用大小（字节）"""
        try:
            payload = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            payload = str(value)
        return len(key.encode("utf-8")) + len(payload.encode("utf-8"))

    async def clear_with_stats(self) -> Dict[str, int]:
        """清空缓存并返回统计"""
        async with self._lock:
            count = len(self._cache)
            size_bytes = sum(
                self._estimate_entry_size(key, value)
                for key, (value, _) in self._cache.items()
            )
            self._cache.clear()
            return {"count": count, "size_bytes": size_bytes}

    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()

    async def invalidate(self, pattern: str = "") -> int:
        """使匹配模式的缓存失效"""
        async with self._lock:
            if not pattern:
                count = len(self._cache)
                self._cache.clear()
                return count

            keys_to_delete = [k for k in self._cache if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
