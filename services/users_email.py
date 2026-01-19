"""
Danbooru API Plugin - Users email operations
"""

from core.models import APIResponse


class UsersEmailMixin:
    """邮箱相关操作"""

    async def get_email(self, user_id: int) -> APIResponse:
        return await self.client.get(f"users/{user_id}/email")

    async def update_email(self, user_id: int, email: str) -> APIResponse:
        data = {"user": {"email": email}}
        return await self.client.put(f"users/{user_id}/email", json_data=data)

    async def verify_email(self, user_id: int) -> APIResponse:
        return await self.client.get(f"users/{user_id}/email/verify")

    async def send_email_confirmation(self, user_id: int) -> APIResponse:
        return await self.client.post(f"users/{user_id}/email/send_confirmation")
