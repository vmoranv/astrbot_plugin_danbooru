"""
Danbooru API Plugin - Saved searches service
"""

from typing import Optional

from .base import BaseService
from ..core.models import APIResponse, PaginationParams


class SavedSearchesService(BaseService):
    """保存的搜索服务"""

    _endpoint_prefix = "saved_searches"

    async def list(
        self,
        query: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """获取保存的搜索列表"""
        params = {}
        if query:
            params["search[query]"] = query
        return await self.client.get(
            "saved_searches",
            params=self._apply_pagination(params, pagination),
        )

    async def create(
        self,
        query: str,
        label_string: Optional[str] = None,
    ) -> APIResponse:
        """创建保存的搜索"""
        data = {
            "saved_search": {
                "query": query,
            }
        }
        if label_string:
            data["saved_search"]["label_string"] = label_string
        return await self.client.post("saved_searches", json_data=data)

    async def update(
        self,
        saved_search_id: int,
        query: Optional[str] = None,
        label_string: Optional[str] = None,
    ) -> APIResponse:
        """更新保存的搜索"""
        data = {"saved_search": {}}
        if query:
            data["saved_search"]["query"] = query
        if label_string:
            data["saved_search"]["label_string"] = label_string
        return await self.client.put(f"saved_searches/{saved_search_id}", json_data=data)

    async def delete(self, saved_search_id: int) -> APIResponse:
        """删除保存的搜索"""
        return await self.client.delete(f"saved_searches/{saved_search_id}")
