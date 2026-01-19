"""
Danbooru API Plugin - Moderation appeal operations
"""

from typing import Optional

from ..core.models import APIResponse, PaginationParams


class ModerationAppealsMixin:
    """帖子申诉操作"""

    async def list_post_appeals(
        self,
        post_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        status: Optional[str] = None,
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
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        return await self.client.get(
            "post_appeals",
            params=self._apply_pagination(params, pagination),
        )

    async def get_post_appeal(self, appeal_id: int) -> APIResponse:
        return await self.client.get(f"post_appeals/{appeal_id}")

    async def create_post_appeal(
        self,
        post_id: int,
        reason: str,
    ) -> APIResponse:
        data = {
            "post_appeal": {
                "post_id": post_id,
                "reason": reason,
            }
        }
        return await self.client.post("post_appeals", json_data=data)

    async def update_post_appeal(
        self,
        appeal_id: int,
        reason: Optional[str] = None,
    ) -> APIResponse:
        data = {"post_appeal": {}}
        if reason:
            data["post_appeal"]["reason"] = reason
        return await self.client.put(f"post_appeals/{appeal_id}", json_data=data)

    async def delete_post_appeal(self, appeal_id: int) -> APIResponse:
        return await self.client.delete(f"post_appeals/{appeal_id}")
