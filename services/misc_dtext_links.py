"""Danbooru API Plugin - DText links service."""

from typing import Optional

from .base import BaseService
from ..core.models import APIResponse, PaginationParams


class DtextLinksService(BaseService):
    """DText links service."""

    _endpoint_prefix = "dtext_links"

    async def list(
        self,
        query: Optional[str] = None,
        link_type: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if query:
            params["search[query]"] = query
        if link_type:
            params["search[type]"] = link_type
        return await self.client.get(
            "dtext_links",
            params=self._apply_pagination(params, pagination),
        )
