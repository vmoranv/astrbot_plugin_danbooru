"""
Danbooru API Plugin - Users feedback operations
"""

from typing import Optional

from ..core.models import APIResponse, PaginationParams


class UsersFeedbacksMixin:
    """用户反馈操作"""

    async def get_feedbacks(
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

    async def create_feedback(
        self,
        user_id: int,
        body: str,
        category: str = "neutral",
    ) -> APIResponse:
        data = {
            "user_feedback": {
                "user_id": user_id,
                "body": body,
                "category": category,
            }
        }
        return await self.client.post("user_feedbacks", json_data=data)

    async def get_feedback(self, feedback_id: int) -> APIResponse:
        return await self.client.get(f"user_feedbacks/{feedback_id}")

    async def edit_feedback(self, feedback_id: int) -> APIResponse:
        return await self.client.get(f"user_feedbacks/{feedback_id}/edit")

    async def update_feedback(
        self,
        feedback_id: int,
        data: dict,
        method: str = "PUT",
    ) -> APIResponse:
        if method.upper() == "PATCH":
            return await self.client.patch(
                f"user_feedbacks/{feedback_id}", json_data=data
            )
        return await self.client.put(f"user_feedbacks/{feedback_id}", json_data=data)
