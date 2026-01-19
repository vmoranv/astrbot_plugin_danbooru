"""
Danbooru API Plugin - Service registry
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from core.client import DanbooruClient
from events.event_bus import EventBus
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


@dataclass
class ServiceRegistry:
    posts: PostsService
    tags: TagsService
    artists: ArtistsService
    artist_commentaries: ArtistCommentariesService
    pools: PoolsService
    comments: CommentsService
    users: UsersService
    notes: NotesService
    wiki: WikiService
    favorites: FavoritesService
    uploads: UploadsService
    forum: ForumService
    moderation: ModerationService
    related_tags: RelatedTagsService
    iqdb: IQDBService
    autocomplete: AutocompleteService
    explore: ExploreService
    status: StatusService
    counts: CountsService
    source: SourceService
    dmails: DmailsService
    saved_searches: SavedSearchesService
    news_updates: NewsUpdatesService
    rate_limits: RateLimitsService
    dtext_preview: DtextPreviewService
    dtext_links: DtextLinksService
    recommended_posts: RecommendedPostsService
    service_map: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(cls, client: DanbooruClient, event_bus: EventBus) -> "ServiceRegistry":
        posts = PostsService(client, event_bus)
        tags = TagsService(client, event_bus)
        artists = ArtistsService(client, event_bus)
        artist_commentaries = ArtistCommentariesService(client, event_bus)
        pools = PoolsService(client, event_bus)
        comments = CommentsService(client, event_bus)
        users = UsersService(client, event_bus)
        notes = NotesService(client, event_bus)
        wiki = WikiService(client, event_bus)
        favorites = FavoritesService(client, event_bus)
        uploads = UploadsService(client, event_bus)
        forum = ForumService(client, event_bus)
        moderation = ModerationService(client, event_bus)
        related_tags = RelatedTagsService(client, event_bus)
        iqdb = IQDBService(client, event_bus)
        autocomplete = AutocompleteService(client, event_bus)
        explore = ExploreService(client, event_bus)
        status = StatusService(client, event_bus)
        counts = CountsService(client, event_bus)
        source = SourceService(client, event_bus)
        dmails = DmailsService(client, event_bus)
        saved_searches = SavedSearchesService(client, event_bus)
        news_updates = NewsUpdatesService(client, event_bus)
        rate_limits = RateLimitsService(client, event_bus)
        dtext_preview = DtextPreviewService(client, event_bus)
        dtext_links = DtextLinksService(client, event_bus)
        recommended_posts = RecommendedPostsService(client, event_bus)

        service_map = {
            "posts": posts,
            "tags": tags,
            "artists": artists,
            "artist_commentaries": artist_commentaries,
            "pools": pools,
            "comments": comments,
            "users": users,
            "notes": notes,
            "wiki": wiki,
            "favorites": favorites,
            "uploads": uploads,
            "forum": forum,
            "moderation": moderation,
            "related_tags": related_tags,
            "iqdb": iqdb,
            "autocomplete": autocomplete,
            "explore": explore,
            "status": status,
            "counts": counts,
            "source": source,
            "dmails": dmails,
            "saved_searches": saved_searches,
            "news_updates": news_updates,
            "rate_limits": rate_limits,
            "dtext_preview": dtext_preview,
            "dtext_links": dtext_links,
            "recommended_posts": recommended_posts,
            "news": news_updates,
            "rate": rate_limits,
            "dtext": dtext_preview,
            "recommended": recommended_posts,
        }

        return cls(
            posts=posts,
            tags=tags,
            artists=artists,
            artist_commentaries=artist_commentaries,
            pools=pools,
            comments=comments,
            users=users,
            notes=notes,
            wiki=wiki,
            favorites=favorites,
            uploads=uploads,
            forum=forum,
            moderation=moderation,
            related_tags=related_tags,
            iqdb=iqdb,
            autocomplete=autocomplete,
            explore=explore,
            status=status,
            counts=counts,
            source=source,
            dmails=dmails,
            saved_searches=saved_searches,
            news_updates=news_updates,
            rate_limits=rate_limits,
            dtext_preview=dtext_preview,
            dtext_links=dtext_links,
            recommended_posts=recommended_posts,
            service_map=service_map,
        )
