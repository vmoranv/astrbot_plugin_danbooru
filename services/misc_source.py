"""
Danbooru API Plugin - Source service
"""

from .base import BaseService
from core.models import APIResponse


class SourceService(BaseService):
    """来源服务"""

    _endpoint_prefix = "source"

    async def get(
        self,
        url: str,
    ) -> APIResponse:
        """获取来源信息"""
        params = {"url": url}
        return await self.client.get("source", params=params)
