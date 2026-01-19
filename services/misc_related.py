"""
Danbooru API Plugin - Related tags service
"""

from typing import Optional

from .base import BaseService
from ..core.models import APIResponse


class RelatedTagsService(BaseService):
    """相关标签服务"""

    _endpoint_prefix = "related_tag"

    async def get(
        self,
        query: str,
        category: Optional[str] = None,
    ) -> APIResponse:
        """
        获取相关标签
        """
        params = {"query": query}
        if category:
            params["category"] = category
        return await self.client.get("related_tag", params=params)

    async def update(
        self,
        query: str,
        category: Optional[str] = None,
    ) -> APIResponse:
        """
        更新相关标签缓存
        """
        data = {"query": query}
        if category:
            data["category"] = category
        return await self.client.put("related_tag", json_data=data)

    async def patch(
        self,
        query: str,
        category: Optional[str] = None,
    ) -> APIResponse:
        data = {"query": query}
        if category:
            data["category"] = category
        return await self.client.patch("related_tag", json_data=data)
