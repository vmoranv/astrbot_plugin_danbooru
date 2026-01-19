"""
Danbooru API Plugin - Posts note/translation operations
"""

from ..core.models import APIResponse


class PostsNotesMixin:
    """Posts note/translation operations."""

    async def copy_notes(self, post_id: int, source_post_id: int) -> APIResponse:
        data = {"other_post_id": source_post_id}
        return await self.client.put(f"posts/{post_id}/copy_notes", json_data=data)

    async def mark_as_translated(
        self,
        post_id: int,
        translated: bool = True,
    ) -> APIResponse:
        data = {"post": {"is_translated": translated}}
        return await self.client.put(f"posts/{post_id}/mark_as_translated", json_data=data)
