"""
Danbooru API Plugin - 事件类型定义
定义所有Danbooru API相关的事件类型
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .event_bus import Event


# ==================== 基础事件类型 ====================

@dataclass
class DanbooruEvent(Event):
    """Danbooru API 基础事件"""
    
    def __init__(
        self,
        event_type: str = "",
        source: str = "danbooru",
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            event_type=event_type,
            source=source,
            data=data or {},
            **kwargs
        )


# ==================== API 请求/响应事件 ====================

@dataclass
class APIRequestEvent(DanbooruEvent):
    """API请求事件"""
    method: str = "GET"
    endpoint: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        self.event_type = "api.request"
        self.data.update({
            "method": self.method,
            "endpoint": self.endpoint,
            "params": self.params,
            "body": self.body,
        })


@dataclass
class APIResponseEvent(DanbooruEvent):
    """API响应事件"""
    method: str = "GET"
    endpoint: str = ""
    status_code: int = 200
    response_data: Optional[Any] = None
    duration_ms: float = 0.0
    from_cache: bool = False
    
    def __post_init__(self):
        self.event_type = "api.response"
        self.data.update({
            "method": self.method,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "from_cache": self.from_cache,
        })


# ==================== Post 事件 ====================

@dataclass
class PostEvent(DanbooruEvent):
    """帖子相关事件基类"""
    post_id: Optional[int] = None
    post_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "post"
        self.data.update({
            "post_id": self.post_id,
            "post_data": self.post_data,
        })


class PostEvents:
    """帖子事件类型常量"""
    SEARCHED = "post.searched"
    FETCHED = "post.fetched"
    CREATED = "post.created"
    UPDATED = "post.updated"
    DELETED = "post.deleted"
    VOTED = "post.voted"
    FAVORITED = "post.favorited"
    UNFAVORITED = "post.unfavorited"
    FLAGGED = "post.flagged"
    APPEALED = "post.appealed"


@dataclass
class PostSearchedEvent(PostEvent):
    """帖子搜索事件"""
    tags: str = ""
    results_count: int = 0
    page: int = 1
    
    def __post_init__(self):
        self.event_type = PostEvents.SEARCHED
        super().__post_init__()
        self.data.update({
            "tags": self.tags,
            "results_count": self.results_count,
            "page": self.page,
        })


@dataclass
class PostFetchedEvent(PostEvent):
    """帖子获取事件"""
    
    def __post_init__(self):
        self.event_type = PostEvents.FETCHED
        super().__post_init__()


@dataclass
class PostVotedEvent(PostEvent):
    """帖子投票事件"""
    score: int = 0
    vote_type: str = "up"  # up, down
    
    def __post_init__(self):
        self.event_type = PostEvents.VOTED
        super().__post_init__()
        self.data.update({
            "score": self.score,
            "vote_type": self.vote_type,
        })


# ==================== Tag 事件 ====================

@dataclass
class TagEvent(DanbooruEvent):
    """标签相关事件基类"""
    tag_id: Optional[int] = None
    tag_name: Optional[str] = None
    tag_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "tag"
        self.data.update({
            "tag_id": self.tag_id,
            "tag_name": self.tag_name,
            "tag_data": self.tag_data,
        })


class TagEvents:
    """标签事件类型常量"""
    SEARCHED = "tag.searched"
    FETCHED = "tag.fetched"
    CREATED = "tag.created"
    UPDATED = "tag.updated"
    ALIASED = "tag.aliased"
    IMPLIED = "tag.implied"


@dataclass
class TagSearchedEvent(TagEvent):
    """标签搜索事件"""
    query: str = ""
    results_count: int = 0
    
    def __post_init__(self):
        self.event_type = TagEvents.SEARCHED
        super().__post_init__()
        self.data.update({
            "query": self.query,
            "results_count": self.results_count,
        })


# ==================== Artist 事件 ====================

@dataclass
class ArtistEvent(DanbooruEvent):
    """艺术家相关事件基类"""
    artist_id: Optional[int] = None
    artist_name: Optional[str] = None
    artist_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "artist"
        self.data.update({
            "artist_id": self.artist_id,
            "artist_name": self.artist_name,
            "artist_data": self.artist_data,
        })


class ArtistEvents:
    """艺术家事件类型常量"""
    SEARCHED = "artist.searched"
    FETCHED = "artist.fetched"
    CREATED = "artist.created"
    UPDATED = "artist.updated"
    BANNED = "artist.banned"
    UNBANNED = "artist.unbanned"


# ==================== Pool 事件 ====================

@dataclass
class PoolEvent(DanbooruEvent):
    """图池相关事件基类"""
    pool_id: Optional[int] = None
    pool_name: Optional[str] = None
    pool_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "pool"
        self.data.update({
            "pool_id": self.pool_id,
            "pool_name": self.pool_name,
            "pool_data": self.pool_data,
        })


class PoolEvents:
    """图池事件类型常量"""
    SEARCHED = "pool.searched"
    FETCHED = "pool.fetched"
    CREATED = "pool.created"
    UPDATED = "pool.updated"
    DELETED = "pool.deleted"
    POST_ADDED = "pool.post_added"
    POST_REMOVED = "pool.post_removed"


# ==================== Comment 事件 ====================

@dataclass
class CommentEvent(DanbooruEvent):
    """评论相关事件基类"""
    comment_id: Optional[int] = None
    post_id: Optional[int] = None
    comment_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "comment"
        self.data.update({
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "comment_data": self.comment_data,
        })


class CommentEvents:
    """评论事件类型常量"""
    SEARCHED = "comment.searched"
    FETCHED = "comment.fetched"
    CREATED = "comment.created"
    UPDATED = "comment.updated"
    DELETED = "comment.deleted"
    VOTED = "comment.voted"


# ==================== User 事件 ====================

@dataclass
class UserEvent(DanbooruEvent):
    """用户相关事件基类"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "user"
        self.data.update({
            "user_id": self.user_id,
            "username": self.username,
            "user_data": self.user_data,
        })


class UserEvents:
    """用户事件类型常量"""
    SEARCHED = "user.searched"
    FETCHED = "user.fetched"
    PROFILE_FETCHED = "user.profile_fetched"
    UPDATED = "user.updated"


# ==================== Search 事件 ====================

@dataclass
class SearchEvent(DanbooruEvent):
    """搜索事件"""
    query: str = ""
    search_type: str = ""  # post, tag, artist, pool, etc.
    results_count: int = 0
    page: int = 1
    filters: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        self.event_type = f"search.{self.search_type}" if self.search_type else "search"
        self.data.update({
            "query": self.query,
            "search_type": self.search_type,
            "results_count": self.results_count,
            "page": self.page,
            "filters": self.filters or {},
        })


# ==================== Cache 事件 ====================

@dataclass
class CacheEvent(DanbooruEvent):
    """缓存事件"""
    cache_key: str = ""
    cache_action: str = ""  # hit, miss, set, invalidate, clear
    ttl: Optional[int] = None
    
    def __post_init__(self):
        self.event_type = f"cache.{self.cache_action}" if self.cache_action else "cache"
        self.data.update({
            "cache_key": self.cache_key,
            "cache_action": self.cache_action,
            "ttl": self.ttl,
        })


class CacheEvents:
    """缓存事件类型常量"""
    HIT = "cache.hit"
    MISS = "cache.miss"
    SET = "cache.set"
    INVALIDATE = "cache.invalidate"
    CLEAR = "cache.clear"


# ==================== Error 事件 ====================

@dataclass
class ErrorEvent(DanbooruEvent):
    """错误事件"""
    error_type: str = ""
    error_message: str = ""
    error_code: Optional[int] = None
    original_event: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    
    def __post_init__(self):
        self.event_type = f"error.{self.error_type}" if self.error_type else "error"
        self.data.update({
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "original_event": self.original_event,
            "stack_trace": self.stack_trace,
        })


class ErrorEvents:
    """错误事件类型常量"""
    API_ERROR = "error.api"
    AUTH_ERROR = "error.auth"
    RATE_LIMIT = "error.rate_limit"
    VALIDATION = "error.validation"
    NETWORK = "error.network"
    HANDLER = "error.handler"


# ==================== Wiki 事件 ====================

@dataclass
class WikiEvent(DanbooruEvent):
    """Wiki相关事件基类"""
    wiki_id: Optional[int] = None
    wiki_title: Optional[str] = None
    wiki_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "wiki"
        self.data.update({
            "wiki_id": self.wiki_id,
            "wiki_title": self.wiki_title,
            "wiki_data": self.wiki_data,
        })


class WikiEvents:
    """Wiki事件类型常量"""
    SEARCHED = "wiki.searched"
    FETCHED = "wiki.fetched"
    CREATED = "wiki.created"
    UPDATED = "wiki.updated"
    DELETED = "wiki.deleted"
    REVERTED = "wiki.reverted"


# ==================== Note 事件 ====================

@dataclass
class NoteEvent(DanbooruEvent):
    """注释相关事件基类"""
    note_id: Optional[int] = None
    post_id: Optional[int] = None
    note_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "note"
        self.data.update({
            "note_id": self.note_id,
            "post_id": self.post_id,
            "note_data": self.note_data,
        })


class NoteEvents:
    """注释事件类型常量"""
    SEARCHED = "note.searched"
    FETCHED = "note.fetched"
    CREATED = "note.created"
    UPDATED = "note.updated"
    DELETED = "note.deleted"
    REVERTED = "note.reverted"


# ==================== Favorite 事件 ====================

@dataclass
class FavoriteEvent(DanbooruEvent):
    """收藏相关事件基类"""
    post_id: Optional[int] = None
    user_id: Optional[int] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "favorite"
        self.data.update({
            "post_id": self.post_id,
            "user_id": self.user_id,
        })


class FavoriteEvents:
    """收藏事件类型常量"""
    ADDED = "favorite.added"
    REMOVED = "favorite.removed"
    LISTED = "favorite.listed"


# ==================== Forum 事件 ====================

@dataclass
class ForumEvent(DanbooruEvent):
    """论坛相关事件基类"""
    topic_id: Optional[int] = None
    post_id: Optional[int] = None
    forum_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "forum"
        self.data.update({
            "topic_id": self.topic_id,
            "post_id": self.post_id,
            "forum_data": self.forum_data,
        })


class ForumEvents:
    """论坛事件类型常量"""
    TOPIC_CREATED = "forum.topic_created"
    TOPIC_UPDATED = "forum.topic_updated"
    TOPIC_DELETED = "forum.topic_deleted"
    POST_CREATED = "forum.post_created"
    POST_UPDATED = "forum.post_updated"
    POST_DELETED = "forum.post_deleted"


# ==================== Upload 事件 ====================

@dataclass
class UploadEvent(DanbooruEvent):
    """上传相关事件"""
    upload_id: Optional[int] = None
    status: str = ""
    post_id: Optional[int] = None
    
    def __post_init__(self):
        if not self.event_type:
            self.event_type = "upload"
        self.data.update({
            "upload_id": self.upload_id,
            "status": self.status,
            "post_id": self.post_id,
        })


class UploadEvents:
    """上传事件类型常量"""
    STARTED = "upload.started"
    COMPLETED = "upload.completed"
    FAILED = "upload.failed"
    PREPROCESSED = "upload.preprocessed"


# ==================== 系统事件 ====================

class SystemEvents:
    """系统事件类型常量"""
    INITIALIZED = "system.initialized"
    SHUTDOWN = "system.shutdown"
    CONFIG_CHANGED = "system.config_changed"
    AUTH_SUCCESS = "system.auth_success"
    AUTH_FAILURE = "system.auth_failure"
    RATE_LIMITED = "system.rate_limited"