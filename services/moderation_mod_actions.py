"""
Danbooru API Plugin - Moderation mod actions operations
"""

from typing import Optional

from core.models import APIResponse, PaginationParams


class ModerationModActionsMixin:
    """管理操作日志"""

    async def list_mod_actions(
        self,
        creator_id: Optional[int] = None,
        category: Optional[str] = None,
        action: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
        **kwargs,
    ) -> APIResponse:
        params = {}
        if creator_id:
            params["search[creator_id]"] = creator_id
        if category:
            params["search[category]"] = category
        if action:
            params["search[action]"] = action
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        return await self.client.get(
            "mod_actions",
            params=self._apply_pagination(params, pagination),
        )

    async def get_mod_action(self, action_id: int) -> APIResponse:
        return await self.client.get(f"mod_actions/{action_id}")

    async def create_mod_action(
        self,
        description: str,
        category: Optional[str] = None,
    ) -> APIResponse:
        data = {
            "mod_action": {
                "description": description,
            }
        }
        if category:
            data["mod_action"]["category"] = category
        return await self.client.post("mod_actions", json_data=data)
