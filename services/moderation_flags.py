"""
Danbooru API Plugin - Moderation flag operations
"""

from typing import Optional

from core.models import APIResponse, PaginationParams


class ModerationFlagsMixin:
    """帖子标记操作"""

    async def list_post_flags(
        self,
        post_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
        **kwargs,
    ) -> APIResponse:
        params = {}
        if post_id:
            params["search[post_id]"] = post_id
        if creator_id:
            params["search[creator_id]"] = creator_id
        if status:
            params["search[status]"] = status
        if category:
            params["search[category]"] = category
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        return await self.client.get(
            "post_flags",
            params=self._apply_pagination(params, pagination),
        )

    async def get_post_flag(self, flag_id: int) -> APIResponse:
        return await self.client.get(f"post_flags/{flag_id}")

    async def create_post_flag(
        self,
        post_id: int,
        reason: str,
        parent_id: Optional[int] = None,
    ) -> APIResponse:
        data = {
            "post_flag": {
                "post_id": post_id,
                "reason": reason,
            }
        }
        if parent_id:
            data["post_flag"]["parent_id"] = parent_id
        return await self.client.post("post_flags", json_data=data)

    async def update_post_flag(
        self,
        flag_id: int,
        reason: Optional[str] = None,
    ) -> APIResponse:
        data = {"post_flag": {}}
        if reason:
            data["post_flag"]["reason"] = reason
        return await self.client.put(f"post_flags/{flag_id}", json_data=data)

    async def delete_post_flag(self, flag_id: int) -> APIResponse:
        return await self.client.delete(f"post_flags/{flag_id}")
