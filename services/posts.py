"""
Danbooru API Plugin - Posts 服务
帖子相关的所有API操作
"""

from .base import VersionedService
from .posts_core import PostsCoreMixin
from .posts_search import PostsSearchMixin
from .posts_votes import PostsVotesMixin
from .posts_versions import PostsVersionsMixin
from .posts_notes import PostsNotesMixin
from .posts_related import PostsRelatedMixin
from .posts_parse import PostsParseMixin


class PostsService(
    PostsCoreMixin,
    PostsSearchMixin,
    PostsVotesMixin,
    PostsVersionsMixin,
    PostsNotesMixin,
    PostsRelatedMixin,
    PostsParseMixin,
    VersionedService,
):
    """帖子服务 - 处理所有帖子相关的API操作"""

    _endpoint_prefix = "posts"
    _versions_endpoint = "post_versions"
