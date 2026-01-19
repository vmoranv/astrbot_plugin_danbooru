"""
Danbooru API Plugin - News updates service
"""

from typing import Optional

from .base import BaseService
from core.models import APIResponse, PaginationParams


class NewsUpdatesService(BaseService):
    """新闻更新服务"""

    _endpoint_prefix = "news_updates"

    async def list(
        self,
        updater_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """获取新闻更新列表"""
        params = {}
        if updater_id:
            params["search[updater_id]"] = updater_id
        return await self.client.get(
            "news_updates",
            params=self._apply_pagination(params, pagination),
        )

    async def get(self, news_id: int) -> APIResponse:
        """获取单个新闻更新"""
        return await self.client.get(f"news_updates/{news_id}")

    async def create(
        self,
        message: str,
    ) -> APIResponse:
        """创建新闻更新"""
        data = {
            "news_update": {
                "message": message,
            }
        }
        return await self.client.post("news_updates", json_data=data)

    async def update(
        self,
        news_id: int,
        message: str,
    ) -> APIResponse:
        """更新新闻"""
        data = {
            "news_update": {
                "message": message,
            }
        }
        return await self.client.put(f"news_updates/{news_id}", json_data=data)

    async def delete(self, news_id: int) -> APIResponse:
        """删除新闻"""
        return await self.client.delete(f"news_updates/{news_id}")
