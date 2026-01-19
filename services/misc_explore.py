"""
Danbooru API Plugin - Explore service
"""

from typing import Optional

from .base import BaseService
from core.models import APIResponse


class ExploreService(BaseService):
    """探索服务 - 热门帖子、策划内容等"""

    _endpoint_prefix = "explore/posts"

    async def popular(
        self,
        date: Optional[str] = None,
        scale: Optional[str] = None,
    ) -> APIResponse:
        """获取热门帖子"""
        params = {}
        if date:
            params["date"] = date
        if scale:
            params["scale"] = scale
        return await self.client.get("explore/posts/popular", params=params)

    async def curated(
        self,
        date: Optional[str] = None,
        scale: Optional[str] = None,
    ) -> APIResponse:
        """获取精选帖子"""
        params = {}
        if date:
            params["date"] = date
        if scale:
            params["scale"] = scale
        return await self.client.get("explore/posts/curated", params=params)

    async def viewed(
        self,
        date: Optional[str] = None,
    ) -> APIResponse:
        """获取浏览量最高的帖子"""
        params = {}
        if date:
            params["date"] = date
        return await self.client.get("explore/posts/viewed", params=params)

    async def searches(
        self,
        date: Optional[str] = None,
    ) -> APIResponse:
        """获取热门搜索"""
        params = {}
        if date:
            params["date"] = date
        return await self.client.get("explore/posts/searches", params=params)

    async def missed_searches(
        self,
        date: Optional[str] = None,
    ) -> APIResponse:
        """获取未命中的搜索"""
        params = {}
        if date:
            params["date"] = date
        return await self.client.get("explore/posts/missed_searches", params=params)
