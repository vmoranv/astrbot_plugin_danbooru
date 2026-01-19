"""
Danbooru API Plugin - Posts related operations
"""

from typing import Optional

from core.models import PaginationParams, APIResponse


class PostsRelatedMixin:
    """Posts related operations."""

    async def similar(self, post_id: int) -> APIResponse:
        return await self.client.get("iqdb_queries", params={"post_id": post_id})

    async def get_events(
        self,
        post_id: int,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = self._apply_pagination({}, pagination)
        return await self.client.get(f"posts/{post_id}/events", params=params)

    async def get_replacements(
        self,
        post_id: Optional[int] = None,
        uploader_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if post_id:
            params["search[post_id]"] = post_id
        if uploader_id:
            params["search[uploader_id]"] = uploader_id
        return await self.client.get(
            "post_replacements",
            params=self._apply_pagination(params, pagination),
        )

    async def list_replacements_for_post(
        self,
        post_id: int,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = self._apply_pagination({}, pagination)
        return await self.client.get(f"posts/{post_id}/replacements", params=params)

    async def new_replacement_for_post(self, post_id: int) -> APIResponse:
        return await self.client.get(f"posts/{post_id}/replacements/new")

    async def create_replacement(
        self,
        post_id: int,
        replacement_url: str,
        final_source: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> APIResponse:
        data = {
            "post_replacement": {
                "replacement_url": replacement_url,
            }
        }
        if final_source:
            data["post_replacement"]["final_source"] = final_source
        if tags:
            data["post_replacement"]["tags"] = tags
        return await self.client.post(f"posts/{post_id}/replacements", json_data=data)

    async def create_post_replacement(self, data: dict) -> APIResponse:
        return await self.client.post("post_replacements", json_data=data)

    async def new_post_replacement(self) -> APIResponse:
        return await self.client.get("post_replacements/new")

    async def update_post_replacement(
        self,
        replacement_id: int,
        data: dict,
        method: str = "PUT",
    ) -> APIResponse:
        if method.upper() == "PATCH":
            return await self.client.patch(
                f"post_replacements/{replacement_id}", json_data=data
            )
        return await self.client.put(
            f"post_replacements/{replacement_id}", json_data=data
        )
