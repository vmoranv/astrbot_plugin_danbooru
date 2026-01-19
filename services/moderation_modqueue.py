"""
Danbooru API Plugin - Moderation modqueue operations
"""

from typing import Optional

from ..core.models import APIResponse, PaginationParams


class ModerationModqueueMixin:
    """审核队列操作"""

    async def get_modqueue(
        self,
        user_id: Optional[int] = None,
        level: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if user_id:
            params["search[user_id]"] = user_id
        if level:
            params["search[level]"] = level
        return await self.client.get(
            "modqueue",
            params=self._apply_pagination(params, pagination),
        )
