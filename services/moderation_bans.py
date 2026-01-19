"""
Danbooru API Plugin - Moderation bans operations
"""

from typing import Optional

from ..core.models import APIResponse, PaginationParams


class ModerationBansMixin:
    """封禁与 IP 封禁操作"""

    async def list_bans(
        self,
        user_id: Optional[int] = None,
        banner_id: Optional[int] = None,
        expired: Optional[bool] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if user_id:
            params["search[user_id]"] = user_id
        if banner_id:
            params["search[banner_id]"] = banner_id
        if expired is not None:
            params["search[expired]"] = str(expired).lower()
        return await self.client.get(
            "bans",
            params=self._apply_pagination(params, pagination),
        )

    async def get_ban(self, ban_id: int) -> APIResponse:
        return await self.client.get(f"bans/{ban_id}")

    async def create_ban(
        self,
        user_id: int,
        reason: str,
        duration: Optional[int] = None,
    ) -> APIResponse:
        data = {
            "ban": {
                "user_id": user_id,
                "reason": reason,
            }
        }
        if duration:
            data["ban"]["duration"] = duration
        return await self.client.post("bans", json_data=data)

    async def update_ban(
        self,
        ban_id: int,
        reason: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> APIResponse:
        data = {"ban": {}}
        if reason:
            data["ban"]["reason"] = reason
        if duration:
            data["ban"]["duration"] = duration
        return await self.client.put(f"bans/{ban_id}", json_data=data)

    async def delete_ban(self, ban_id: int) -> APIResponse:
        return await self.client.delete(f"bans/{ban_id}")

    async def list_ip_bans(
        self,
        ip_addr: Optional[str] = None,
        banner_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if ip_addr:
            params["search[ip_addr]"] = ip_addr
        if banner_id:
            params["search[banner_id]"] = banner_id
        return await self.client.get(
            "ip_bans",
            params=self._apply_pagination(params, pagination),
        )

    async def create_ip_ban(
        self,
        ip_addr: str,
        reason: str,
    ) -> APIResponse:
        data = {
            "ip_ban": {
                "ip_addr": ip_addr,
                "reason": reason,
            }
        }
        return await self.client.post("ip_bans", json_data=data)

    async def update_ip_ban(
        self,
        ip_ban_id: int,
        reason: Optional[str] = None,
    ) -> APIResponse:
        data = {"ip_ban": {}}
        if reason:
            data["ip_ban"]["reason"] = reason
        return await self.client.put(f"ip_bans/{ip_ban_id}", json_data=data)
