"""
Danbooru API Plugin - Posts version operations
"""

from typing import Optional

from ..core.models import PaginationParams, APIResponse


class PostsVersionsMixin:
    """Posts version operations."""

    async def revert(self, post_id: int, version_id: Optional[int] = None) -> APIResponse:
        data = {}
        if version_id:
            data["version_id"] = version_id
        return await self.client.put(f"posts/{post_id}/revert", json_data=data)

    async def get_versions(
        self,
        post_id: Optional[int] = None,
        updater_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if post_id:
            params["search[post_id]"] = post_id
        if updater_id:
            params["search[updater_id]"] = updater_id
        return await self.client.get(
            "post_versions",
            params=self._apply_pagination(params, pagination),
        )

    async def search_versions(
        self,
        changed_tags: Optional[str] = None,
        added_tags: Optional[str] = None,
        removed_tags: Optional[str] = None,
        **kwargs,
    ) -> APIResponse:
        params = {}
        if changed_tags:
            params["search[changed_tags]"] = changed_tags
        if added_tags:
            params["search[added_tags]"] = added_tags
        if removed_tags:
            params["search[removed_tags]"] = removed_tags
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        return await self.client.get("post_versions/search", params=params)

    async def undo_version(self, version_id: int) -> APIResponse:
        """撤销指定版本"""
        return await self.client.put(f"post_versions/{version_id}/undo")
