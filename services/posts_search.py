"""
Danbooru API Plugin - Posts search helpers
"""

from typing import Optional, Dict, Any

from ..core.models import PaginationParams, APIResponse, PostSearchParams


class PostsSearchMixin:
    """Posts search operations."""

    async def search(
        self,
        search_params: Optional[PostSearchParams] = None,
        pagination: Optional[PaginationParams] = None,
        **kwargs,
    ) -> APIResponse:
        params: Dict[str, Any] = {}
        if search_params:
            params.update(search_params.to_params())

        for key, value in kwargs.items():
            if value is not None:
                if not key.startswith("search["):
                    params[f"search[{key}]"] = value
                else:
                    params[key] = value

        return await self._list(params=params, pagination=pagination)

    async def count(self, tags: Optional[str] = None) -> APIResponse:
        params = {}
        if tags:
            params["tags"] = tags
        return await self.client.get("counts/posts", params=params)
