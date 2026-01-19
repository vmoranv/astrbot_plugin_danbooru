"""
Danbooru API Plugin - Moderation bulk update operations
"""

from typing import Optional

from core.models import APIResponse, PaginationParams


class ModerationBulkUpdatesMixin:
    """批量更新请求操作"""

    async def list_bulk_update_requests(
        self,
        user_id: Optional[int] = None,
        approver_id: Optional[int] = None,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if user_id:
            params["search[user_id]"] = user_id
        if approver_id:
            params["search[approver_id]"] = approver_id
        if status:
            params["search[status]"] = status
        return await self.client.get(
            "bulk_update_requests",
            params=self._apply_pagination(params, pagination),
        )

    async def get_bulk_update_request(self, request_id: int) -> APIResponse:
        return await self.client.get(f"bulk_update_requests/{request_id}")

    async def create_bulk_update_request(
        self,
        script: str,
        title: str,
        reason: Optional[str] = None,
        forum_topic_id: Optional[int] = None,
    ) -> APIResponse:
        data = {
            "bulk_update_request": {
                "script": script,
                "title": title,
            }
        }
        if reason:
            data["bulk_update_request"]["reason"] = reason
        if forum_topic_id:
            data["bulk_update_request"]["forum_topic_id"] = forum_topic_id
        return await self.client.post("bulk_update_requests", json_data=data)

    async def approve_bulk_update_request(self, request_id: int) -> APIResponse:
        return await self.client.post(f"bulk_update_requests/{request_id}/approve")

    async def update_bulk_update_request(
        self,
        request_id: int,
        script: Optional[str] = None,
        title: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> APIResponse:
        data = {"bulk_update_request": {}}
        if script:
            data["bulk_update_request"]["script"] = script
        if title:
            data["bulk_update_request"]["title"] = title
        if reason:
            data["bulk_update_request"]["reason"] = reason
        return await self.client.put(f"bulk_update_requests/{request_id}", json_data=data)

    async def delete_bulk_update_request(self, request_id: int) -> APIResponse:
        return await self.client.delete(f"bulk_update_requests/{request_id}")
