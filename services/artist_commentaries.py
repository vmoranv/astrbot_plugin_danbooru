"""Danbooru API Plugin - Artist commentaries service."""

from typing import Optional

from .base import BaseService
from core.models import APIResponse, PaginationParams


class ArtistCommentariesService(BaseService):
    """Artist commentary related operations."""

    _endpoint_prefix = "artist_commentaries"

    async def list(
        self,
        pagination: Optional[PaginationParams] = None,
        **kwargs,
    ) -> APIResponse:
        params = {}
        for key, value in kwargs.items():
            if value is not None:
                if not key.startswith("search["):
                    params[f"search[{key}]"] = value
                else:
                    params[key] = value
        return await self.client.get(
            "artist_commentaries",
            params=self._apply_pagination(params, pagination),
        )

    async def search(
        self,
        pagination: Optional[PaginationParams] = None,
        **kwargs,
    ) -> APIResponse:
        params = {}
        for key, value in kwargs.items():
            if value is not None:
                if not key.startswith("search["):
                    params[f"search[{key}]"] = value
                else:
                    params[key] = value
        return await self.client.get(
            "artist_commentaries/search",
            params=self._apply_pagination(params, pagination),
        )

    async def get(self, commentary_id: int) -> APIResponse:
        return await self.client.get(f"artist_commentaries/{commentary_id}")

    async def get_by_post(self, post_id: int) -> APIResponse:
        return await self.client.get(f"posts/{post_id}/artist_commentary")

    async def create_or_update_by_post(self, post_id: int, data: dict) -> APIResponse:
        return await self.client.put(
            f"posts/{post_id}/artist_commentary/create_or_update", json_data=data
        )

    async def revert_by_post(
        self,
        post_id: int,
        version_id: Optional[int] = None,
    ) -> APIResponse:
        payload = {"version_id": version_id} if version_id else {}
        return await self.client.put(
            f"posts/{post_id}/artist_commentary/revert", json_data=payload
        )

    async def revert(self, commentary_id: int, version_id: Optional[int] = None) -> APIResponse:
        payload = {"version_id": version_id} if version_id else {}
        return await self.client.put(
            f"artist_commentaries/{commentary_id}/revert", json_data=payload
        )

    async def list_versions(
        self,
        pagination: Optional[PaginationParams] = None,
        **kwargs,
    ) -> APIResponse:
        params = {}
        for key, value in kwargs.items():
            if value is not None:
                if not key.startswith("search["):
                    params[f"search[{key}]"] = value
                else:
                    params[key] = value
        return await self.client.get(
            "artist_commentary_versions",
            params=self._apply_pagination(params, pagination),
        )

    async def get_version(self, version_id: int) -> APIResponse:
        return await self.client.get(f"artist_commentary_versions/{version_id}")
