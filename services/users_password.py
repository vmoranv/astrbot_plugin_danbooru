"""
Danbooru API Plugin - Users password operations
"""

from ..core.models import APIResponse


class UsersPasswordMixin:
    """密码相关操作"""

    async def update_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        new_password_confirmation: str,
    ) -> APIResponse:
        data = {
            "user": {
                "old_password": old_password,
                "password": new_password,
                "password_confirmation": new_password_confirmation,
            }
        }
        return await self.client.put(f"users/{user_id}/password", json_data=data)

    async def request_password_reset(self, email: str) -> APIResponse:
        data = {"user": {"email": email}}
        return await self.client.post("password_reset", json_data=data)
