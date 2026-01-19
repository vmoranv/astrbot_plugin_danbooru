"""
Danbooru API Plugin - 服务层模块
提供所有API服务的封装
"""

from .base import BaseService, CRUDService, SearchableService, VersionedService
from .posts import PostsService
from .tags import TagsService
from .artists import ArtistsService
from .artist_commentaries import ArtistCommentariesService
from .pools import PoolsService
from .comments import CommentsService
from .users import UsersService
from .notes import NotesService
from .wiki import WikiService
from .favorites import FavoritesService
from .uploads import UploadsService
from .forum import ForumService
from .moderation import ModerationService
from .misc import (
    RelatedTagsService,
    IQDBService,
    AutocompleteService,
    ExploreService,
    StatusService,
    CountsService,
    SourceService,
    DmailsService,
    SavedSearchesService,
    NewsUpdatesService,
    RateLimitsService,
    DtextPreviewService,
    DtextLinksService,
    RecommendedPostsService,
)
from .subscriptions import SubscriptionsService

__all__ = [
    # Base
    "BaseService",
    "CRUDService",
    "SearchableService",
    "VersionedService",
    # Core Services
    "PostsService",
    "TagsService",
    "ArtistsService",
    "ArtistCommentariesService",
    "PoolsService",
    "CommentsService",
    "UsersService",
    "NotesService",
    "WikiService",
    "FavoritesService",
    "UploadsService",
    "ForumService",
    "ModerationService",
    # Misc Services
    "RelatedTagsService",
    "IQDBService",
    "AutocompleteService",
    "ExploreService",
    "StatusService",
    "CountsService",
    "SourceService",
    "DmailsService",
    "SavedSearchesService",
    "NewsUpdatesService",
    "RateLimitsService",
    "DtextPreviewService",
    "DtextLinksService",
    "RecommendedPostsService",
    "SubscriptionsService",
]
