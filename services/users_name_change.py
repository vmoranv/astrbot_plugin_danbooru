"""
Danbooru API Plugin - Users name change operations
"""

from typing import Optional

from ..core.models import APIResponse, PaginationParams


class UsersNameChangeMixin:
    """用户改名请求操作"""

    async def get_name_change_requests(
        self,
        user_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if user_id:
            params["search[user_id]"] = user_id
        return await self.client.get(
            "user_name_change_requests",
            params=self._apply_pagination(params, pagination),
        )

    async def create_name_change_request(
        self,
        desired_name: str,
    ) -> APIResponse:
        data = {
            "user_name_change_request": {
                "desired_name": desired_name,
            }
        }
        return await self.client.post("user_name_change_requests", json_data=data)

    async def get_name_change_request(self, request_id: int) -> APIResponse:
        return await self.client.get(f"user_name_change_requests/{request_id}")
