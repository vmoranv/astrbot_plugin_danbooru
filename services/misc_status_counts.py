"""
Danbooru API Plugin - Status/Counts/Rate limits services
"""

from typing import Optional

from .base import BaseService
from core.models import APIResponse, PaginationParams


class StatusService(BaseService):
    """状态服务"""

    _endpoint_prefix = "status"

    async def get(self) -> APIResponse:
        """获取系统状态"""
        return await self.client.get("status")


class CountsService(BaseService):
    """计数服务"""

    _endpoint_prefix = "counts"

    async def list(self, pagination: Optional[PaginationParams] = None) -> APIResponse:
        params = self._apply_pagination({}, pagination)
        return await self.client.get("counts", params=params)

    async def get(self, count_id: int) -> APIResponse:
        return await self.client.get(f"counts/{count_id}")

    async def create(self, data: dict) -> APIResponse:
        return await self.client.post("counts", json_data=data)

    async def update(self, count_id: int, data: dict, method: str = "PUT") -> APIResponse:
        if method.upper() == "PATCH":
            return await self.client.patch(f"counts/{count_id}", json_data=data)
        return await self.client.put(f"counts/{count_id}", json_data=data)

    async def delete(self, count_id: int) -> APIResponse:
        return await self.client.delete(f"counts/{count_id}")

    async def posts(
        self,
        tags: Optional[str] = None,
    ) -> APIResponse:
        """获取帖子计数"""
        params = {}
        if tags:
            params["tags"] = tags
        return await self.client.get("counts/posts", params=params)


class RateLimitsService(BaseService):
    """速率限制服务"""

    _endpoint_prefix = "rate_limits"

    async def get(self) -> APIResponse:
        """获取当前速率限制状态"""
        return await self.client.get("rate_limits")
