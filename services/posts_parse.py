"""
Danbooru API Plugin - Posts parsing helpers
"""

from typing import Dict, Any, List, Optional

from core.models import Post


class PostsParseMixin:
    """Posts parsing helpers."""

    def parse_post(self, data: Dict[str, Any]) -> Post:
        return Post.from_dict(data)

    def parse_posts(self, data: List[Dict[str, Any]]) -> List[Post]:
        return [Post.from_dict(item) for item in data]

    async def get_parsed(self, post_id: int) -> Optional[Post]:
        response = await self.get(post_id)
        if response.success and response.data:
            return self.parse_post(response.data)
        return None

    async def list_parsed(
        self,
        tags: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> List[Post]:
        response = await self.list(tags=tags, page=page, limit=limit, **kwargs)
        if response.success and isinstance(response.data, list):
            return self.parse_posts(response.data)
        return []
