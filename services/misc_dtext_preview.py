"""
Danbooru API Plugin - DText preview service
"""

from .base import BaseService
from core.models import APIResponse


class DtextPreviewService(BaseService):
    """DText预览服务"""

    _endpoint_prefix = "dtext_preview"

    async def preview(
        self,
        body: str,
    ) -> APIResponse:
        """预览DText渲染结果"""
        data = {"body": body}
        return await self.client.post("dtext_preview", json_data=data)
