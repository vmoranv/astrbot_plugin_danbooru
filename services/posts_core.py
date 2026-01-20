"""
Danbooru API Plugin - Posts core operations
"""

from typing import Optional, Dict, Any, Union

from ..core.models import PaginationParams, APIResponse, Rating
from ..events.event_types import (
    PostSearchedEvent,
    PostFetchedEvent,
    PostEvent,
    PostEvents,
)


class PostsCoreMixin:
    """Posts core CRUD operations."""

    async def list(
        self,
        tags: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> APIResponse:
        params: Dict[str, Any] = {}
        if tags:
            params["tags"] = tags

        pagination = PaginationParams(page=page, limit=limit)

        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value

        response = await self._list(params=params, pagination=pagination)
        if response.success:
            await self._emit_event(PostSearchedEvent(
                tags=tags or "",
                results_count=len(response.data) if isinstance(response.data, list) else 0,
                page=page or 1,
            ))
        return response

    async def get(self, post_id: int) -> APIResponse:
        response = await self._get(post_id)
        if response.success:
            await self._emit_event(PostFetchedEvent(
                post_id=post_id,
                post_data=response.data,
            ))
        return response

    async def random(self, tags: Optional[str] = None) -> APIResponse:
        params = {}
        if tags:
            params["tags"] = tags
        return await self.client.get(
            f"{self._endpoint_prefix}/random",
            params=params,
            use_cache=False,
        )

    async def show_seq(self, post_id: int) -> APIResponse:
        """获取帖子序列信息"""
        return await self.client.get(f"posts/{post_id}/show_seq")

    async def update(
        self,
        post_id: int,
        tag_string: Optional[str] = None,
        rating: Optional[Union[str, Rating]] = None,
        source: Optional[str] = None,
        parent_id: Optional[int] = None,
        **kwargs,
    ) -> APIResponse:
        data = {"post": {}}
        if tag_string is not None:
            data["post"]["tag_string"] = tag_string
        if rating is not None:
            data["post"]["rating"] = rating.value if isinstance(rating, Rating) else rating
        if source is not None:
            data["post"]["source"] = source
        if parent_id is not None:
            data["post"]["parent_id"] = parent_id

        for key, value in kwargs.items():
            if value is not None:
                data["post"][key] = value

        response = await self._update(post_id, data)
        if response.success:
            await self._emit_event(PostEvent(
                event_type=PostEvents.UPDATED,
                post_id=post_id,
                post_data=response.data,
            ))
        return response

    async def delete(self, post_id: int) -> APIResponse:
        response = await self._delete(post_id)
        if response.success:
            await self._emit_event(PostEvent(
                event_type=PostEvents.DELETED,
                post_id=post_id,
            ))
        return response
