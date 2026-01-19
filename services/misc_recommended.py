"""
Danbooru API Plugin - Recommended posts service
"""

from typing import Optional

from .base import BaseService
from core.models import APIResponse, PaginationParams


class RecommendedPostsService(BaseService):
    """推荐帖子服务"""

    _endpoint_prefix = "recommended_posts"

    async def list(
        self,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """获取推荐帖子"""
        return await self.client.get(
            "recommended_posts",
            params=self._apply_pagination({}, pagination),
        )
