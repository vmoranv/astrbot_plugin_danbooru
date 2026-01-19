"""
Danbooru API Plugin - Moderation reports operations
"""

from typing import Optional

from ..core.models import APIResponse, PaginationParams


class ModerationReportsMixin:
    """举报操作"""

    async def list_moderation_reports(
        self,
        model_type: Optional[str] = None,
        model_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if model_type:
            params["search[model_type]"] = model_type
        if model_id:
            params["search[model_id]"] = model_id
        if creator_id:
            params["search[creator_id]"] = creator_id
        if status:
            params["search[status]"] = status
        return await self.client.get(
            "moderation_reports",
            params=self._apply_pagination(params, pagination),
        )

    async def get_moderation_report(self, report_id: int) -> APIResponse:
        return await self.client.get(f"moderation_reports/{report_id}")

    async def create_moderation_report(
        self,
        model_type: str,
        model_id: int,
        reason: str,
    ) -> APIResponse:
        data = {
            "moderation_report": {
                "model_type": model_type,
                "model_id": model_id,
                "reason": reason,
            }
        }
        return await self.client.post("moderation_reports", json_data=data)
