"""
Danbooru API Plugin - Users API key operations
"""

from ..core.models import APIResponse


class UsersApiKeyMixin:
    """API Key 操作"""

    async def get_api_key(self, user_id: int) -> APIResponse:
        return await self.client.get(f"users/{user_id}/api_key")

    async def view_api_key(self, user_id: int, password: str) -> APIResponse:
        data = {"user": {"password": password}}
        return await self.client.post(f"users/{user_id}/api_key/view", json_data=data)

    async def regenerate_api_key(self, user_id: int) -> APIResponse:
        return await self.client.put(f"users/{user_id}/api_key")

    async def delete_api_key(self, user_id: int) -> APIResponse:
        return await self.client.delete(f"users/{user_id}/api_key")
