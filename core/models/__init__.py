"""
Danbooru API Plugin - 数据模型模块
定义API请求/响应的数据模型和通用结构

模块结构:
- base: 基础模型（枚举、分页、搜索参数、API响应）
- posts: Post相关模型
- tags: Tag相关模型
- artists: Artist相关模型
- pools: Pool相关模型
- comments: Comment相关模型
- users: User相关模型
- notes: Note相关模型
- wiki: Wiki相关模型
- favorites: Favorite相关模型
- forum: Forum相关模型
- moderation: 审核相关模型
- uploads: Upload相关模型
- versions: 版本相关模型
- misc: 杂项模型
"""

# Base models
from .base import (
    Rating,
    TagCategory,
    PostStatus,
    OrderDirection,
    PaginationParams,
    SearchParams,
    RateLimitInfo,
    APIResponse,
)

# Post models
from .posts import (
    Post,
    PostSearchParams,
)

# Tag models
from .tags import (
    Tag,
    TagSearchParams,
    RelatedTag,
    TagAlias,
    TagImplication,
)

# Artist models
from .artists import (
    Artist,
    ArtistSearchParams,
    ArtistCommentary,
)

# Pool models
from .pools import (
    Pool,
    PoolSearchParams,
)

# Comment models
from .comments import (
    Comment,
    CommentSearchParams,
)

# User models
from .users import (
    User,
    UserSearchParams,
)

# Note models
from .notes import (
    Note,
    NoteSearchParams,
)

# Wiki models
from .wiki import (
    WikiPage,
    WikiSearchParams,
)

# Favorite models
from .favorites import (
    Favorite,
    FavoriteGroup,
)

# Forum models
from .forum import (
    ForumTopic,
    ForumPost,
)

# Moderation models
from .moderation import (
    PostFlag,
    PostAppeal,
    Ban,
    ModAction,
    BulkUpdateRequest,
)

# Upload models
from .uploads import (
    Upload,
)

# Version models
from .versions import (
    PostVersion,
)

# Misc models
from .misc import (
    Dmail,
    SavedSearch,
    IPAddress,
)

# Type variable for generic types
from typing import TypeVar
T = TypeVar('T')

__all__ = [
    # Base
    'Rating',
    'TagCategory',
    'PostStatus',
    'OrderDirection',
    'PaginationParams',
    'SearchParams',
    'RateLimitInfo',
    'APIResponse',
    'T',
    # Posts
    'Post',
    'PostSearchParams',
    # Tags
    'Tag',
    'TagSearchParams',
    'RelatedTag',
    'TagAlias',
    'TagImplication',
    # Artists
    'Artist',
    'ArtistSearchParams',
    'ArtistCommentary',
    # Pools
    'Pool',
    'PoolSearchParams',
    # Comments
    'Comment',
    'CommentSearchParams',
    # Users
    'User',
    'UserSearchParams',
    # Notes
    'Note',
    'NoteSearchParams',
    # Wiki
    'WikiPage',
    'WikiSearchParams',
    # Favorites
    'Favorite',
    'FavoriteGroup',
    # Forum
    'ForumTopic',
    'ForumPost',
    # Moderation
    'PostFlag',
    'PostAppeal',
    'Ban',
    'ModAction',
    'BulkUpdateRequest',
    # Uploads
    'Upload',
    # Versions
    'PostVersion',
    # Misc
    'Dmail',
    'SavedSearch',
    'IPAddress',
]