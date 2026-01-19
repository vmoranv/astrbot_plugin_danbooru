"""
Danbooru API Plugin - Moderation approvals operations
"""

from typing import Optional

from core.models import APIResponse, PaginationParams


class ModerationApprovalsMixin:
    """帖子批准/不批准操作"""

    async def list_post_approvals(
        self,
        post_id: Optional[int] = None,
        user_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if post_id:
            params["search[post_id]"] = post_id
        if user_id:
            params["search[user_id]"] = user_id
        return await self.client.get(
            "post_approvals",
            params=self._apply_pagination(params, pagination),
        )

    async def create_post_approval(self, post_id: int) -> APIResponse:
        data = {
            "post_approval": {
                "post_id": post_id,
            }
        }
        return await self.client.post("post_approvals", json_data=data)

    async def list_post_disapprovals(
        self,
        post_id: Optional[int] = None,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if post_id:
            params["search[post_id]"] = post_id
        if user_id:
            params["search[user_id]"] = user_id
        if reason:
            params["search[reason]"] = reason
        return await self.client.get(
            "post_disapprovals",
            params=self._apply_pagination(params, pagination),
        )

    async def get_post_disapproval(self, disapproval_id: int) -> APIResponse:
        return await self.client.get(f"post_disapprovals/{disapproval_id}")

    async def create_post_disapproval(
        self,
        post_id: int,
        reason: str,
    ) -> APIResponse:
        data = {
            "post_disapproval": {
                "post_id": post_id,
                "reason": reason,
            }
        }
        return await self.client.post("post_disapprovals", json_data=data)
