"""
Danbooru API Plugin - IQDB service
"""

from typing import Optional

from .base import BaseService
from core.models import APIResponse


class IQDBService(BaseService):
    """IQDB（图像相似度搜索）服务"""

    _endpoint_prefix = "iqdb_queries"

    async def search_by_post(
        self,
        post_id: int,
    ) -> APIResponse:
        """通过帖子ID搜索相似图片"""
        return await self.client.get("iqdb_queries", params={"post_id": post_id})

    async def search_by_url(
        self,
        url: str,
    ) -> APIResponse:
        """通过URL搜索相似图片"""
        data = {"url": url}
        return await self.client.post("iqdb_queries", json_data=data)

    async def search_by_file(
        self,
        file: str,
    ) -> APIResponse:
        """通过文件搜索相似图片"""
        data = {"file": file}
        return await self.client.post("iqdb_queries", json_data=data)

    async def preview(
        self,
        url: Optional[str] = None,
        file: Optional[str] = None,
    ) -> APIResponse:
        """预览IQDB搜索结果"""
        params = {}
        if url:
            params["url"] = url
        if file:
            params["file"] = file
        return await self.client.get("iqdb_queries/preview", params=params)
