"""
Danbooru API Plugin - Dmails service
"""

from typing import Optional

from .base import BaseService
from ..core.models import APIResponse, PaginationParams


class DmailsService(BaseService):
    """私信服务"""

    _endpoint_prefix = "dmails"

    async def list(
        self,
        from_id: Optional[int] = None,
        to_id: Optional[int] = None,
        title_matches: Optional[str] = None,
        is_read: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """获取私信列表"""
        params = {}
        if from_id:
            params["search[from_id]"] = from_id
        if to_id:
            params["search[to_id]"] = to_id
        if title_matches:
            params["search[title_matches]"] = title_matches
        if is_read is not None:
            params["search[is_read]"] = str(is_read).lower()
        if is_deleted is not None:
            params["search[is_deleted]"] = str(is_deleted).lower()

        return await self.client.get(
            "dmails",
            params=self._apply_pagination(params, pagination),
        )

    async def get(self, dmail_id: int) -> APIResponse:
        """获取单个私信"""
        return await self.client.get(f"dmails/{dmail_id}")

    async def create(
        self,
        to_name: str,
        title: str,
        body: str,
    ) -> APIResponse:
        """发送私信"""
        data = {
            "dmail": {
                "to_name": to_name,
                "title": title,
                "body": body,
            }
        }
        return await self.client.post("dmails", json_data=data)

    async def update(
        self,
        dmail_id: int,
        is_read: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
    ) -> APIResponse:
        """更新私信状态"""
        data = {"dmail": {}}
        if is_read is not None:
            data["dmail"]["is_read"] = is_read
        if is_deleted is not None:
            data["dmail"]["is_deleted"] = is_deleted
        return await self.client.put(f"dmails/{dmail_id}", json_data=data)

    async def mark_all_as_read(self) -> APIResponse:
        """标记所有私信为已读"""
        return await self.client.post("dmails/mark_all_as_read")
