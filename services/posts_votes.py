"""
Danbooru API Plugin - Posts voting operations
"""

from typing import Optional

from ..core.models import PaginationParams, APIResponse
from ..events.event_types import PostVotedEvent


class PostsVotesMixin:
    """Posts voting operations."""

    async def vote(self, post_id: int, score: int = 1) -> APIResponse:
        data = {"score": score}
        response = await self.client.post(f"posts/{post_id}/votes", json_data=data)
        if response.success:
            await self._emit_event(PostVotedEvent(
                post_id=post_id,
                score=score,
                vote_type="up" if score > 0 else "down",
            ))
        return response

    async def unvote(self, post_id: int) -> APIResponse:
        return await self.client.delete(f"posts/{post_id}/votes")

    async def get_votes(
        self,
        post_id: Optional[int] = None,
        user_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        params = {}
        if post_id:
            params["search[post_id]"] = post_id
        if user_id:
            params["search[user_id]"] = user_id
        return await self.client.get(
            "post_votes",
            params=self._apply_pagination(params, pagination),
        )
