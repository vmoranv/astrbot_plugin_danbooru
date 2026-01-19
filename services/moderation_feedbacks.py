"""
Danbooru API Plugin - Moderation user feedback operations
"""

from typing import Optional

from core.models import APIResponse, PaginationParams


class ModerationFeedbacksMixin:
    """用户反馈操作"""

    async def list_user_feedbacks(
        self,
        user_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        category: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if user_id:
            params["search[user_id]"] = user_id
        if creator_id:
            params["search[creator_id]"] = creator_id
        if category:
            params["search[category]"] = category
        return await self.client.get(
            "user_feedbacks",
            params=self._apply_pagination(params, pagination),
        )

    async def get_user_feedback(self, feedback_id: int) -> APIResponse:
        return await self.client.get(f"user_feedbacks/{feedback_id}")

    async def create_user_feedback(
        self,
        user_id: int,
        category: str,
        body: str,
    ) -> APIResponse:
        data = {
            "user_feedback": {
                "user_id": user_id,
                "category": category,
                "body": body,
            }
        }
        return await self.client.post("user_feedbacks", json_data=data)

    async def update_user_feedback(
        self,
        feedback_id: int,
        category: Optional[str] = None,
        body: Optional[str] = None,
    ) -> APIResponse:
        data = {"user_feedback": {}}
        if category:
            data["user_feedback"]["category"] = category
        if body:
            data["user_feedback"]["body"] = body
        return await self.client.put(f"user_feedbacks/{feedback_id}", json_data=data)
