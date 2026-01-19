"""
Danbooru API Plugin - Users core operations
"""

from typing import Optional

from core.models import APIResponse, PaginationParams
from events.event_types import UserEvent, UserEvents


class UsersCoreMixin:
    """用户基础操作"""

    async def list(
        self,
        name: Optional[str] = None,
        name_matches: Optional[str] = None,
        level: Optional[int] = None,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None,
        is_banned: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        **kwargs,
    ) -> APIResponse:
        params = {}
        if name:
            params["search[name]"] = name
        if name_matches:
            params["search[name_matches]"] = name_matches
        if level is not None:
            params["search[level]"] = level
        if min_level is not None:
            params["search[min_level]"] = min_level
        if max_level is not None:
            params["search[max_level]"] = max_level
        if is_banned is not None:
            params["search[is_banned]"] = str(is_banned).lower()
        if order:
            params["search[order]"] = order
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        pagination = PaginationParams(page=page, limit=limit)
        response = await self._list(params=params, pagination=pagination)
        if response.success:
            await self._emit_event(UserEvent(
                event_type=UserEvents.SEARCHED,
                username=name_matches or name,
            ))
        return response

    async def get(self, user_id: int) -> APIResponse:
        response = await self._get(user_id)
        if response.success:
            await self._emit_event(UserEvent(
                event_type=UserEvents.FETCHED,
                user_id=user_id,
                user_data=response.data,
            ))
        return response

    async def create(
        self,
        name: str,
        password: str,
        password_confirmation: str,
    ) -> APIResponse:
        data = {
            "user": {
                "name": name,
                "password": password,
                "password_confirmation": password_confirmation,
            }
        }
        return await self._create(data)

    async def update(
        self,
        user_id: int,
        **kwargs,
    ) -> APIResponse:
        data = {"user": kwargs}
        response = await self._update(user_id, data)
        if response.success:
            await self._emit_event(UserEvent(
                event_type=UserEvents.UPDATED,
                user_id=user_id,
                user_data=response.data,
            ))
        return response
