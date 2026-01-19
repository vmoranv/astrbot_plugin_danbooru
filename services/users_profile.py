"""
Danbooru API Plugin - Users profile operations
"""

from ..core.models import APIResponse
from ..events.event_types import UserEvent, UserEvents


class UsersProfileMixin:
    """个人资料相关操作"""

    async def get_profile(self) -> APIResponse:
        response = await self.client.get("profile")
        if response.success:
            await self._emit_event(UserEvent(
                event_type=UserEvents.PROFILE_FETCHED,
                user_data=response.data,
            ))
        return response

    async def get_settings(self) -> APIResponse:
        return await self.client.get("settings")

    async def get_custom_style(self) -> APIResponse:
        return await self.client.get("users/custom_style")
