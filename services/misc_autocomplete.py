"""
Danbooru API Plugin - Autocomplete service
"""

from .base import BaseService
from ..core.models import APIResponse


class AutocompleteService(BaseService):
    """自动补全服务"""

    _endpoint_prefix = "autocomplete"

    async def search(
        self,
        query: str,
        search_type: str = "tag_query",
        limit: int = 10,
    ) -> APIResponse:
        """自动补全搜索"""
        params = {
            "search[query]": query,
            "search[type]": search_type,
            "limit": limit,
        }
        return await self.client.get("autocomplete", params=params)

    async def tag(
        self,
        query: str,
        limit: int = 10,
    ) -> APIResponse:
        """标签自动补全"""
        return await self.search(query, search_type="tag_query", limit=limit)

    async def artist(
        self,
        query: str,
        limit: int = 10,
    ) -> APIResponse:
        """艺术家自动补全"""
        return await self.search(query, search_type="artist", limit=limit)

    async def wiki(
        self,
        query: str,
        limit: int = 10,
    ) -> APIResponse:
        """Wiki页面自动补全"""
        return await self.search(query, search_type="wiki_page", limit=limit)

    async def user(
        self,
        query: str,
        limit: int = 10,
    ) -> APIResponse:
        """用户自动补全"""
        return await self.search(query, search_type="user", limit=limit)

    async def pool(
        self,
        query: str,
        limit: int = 10,
    ) -> APIResponse:
        """池自动补全"""
        return await self.search(query, search_type="pool", limit=limit)
