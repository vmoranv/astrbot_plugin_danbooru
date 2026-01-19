"""
Danbooru API Plugin - Comment 数据模型
定义评论相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .base import SearchParams


@dataclass
class Comment:
    """评论模型"""
    id: int
    post_id: int
    creator_id: int
    body: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    score: int = 0
    is_deleted: bool = False
    is_sticky: bool = False
    do_not_bump_post: bool = False
    updater_id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CommentSearchParams(SearchParams):
    """评论搜索参数"""
    body_matches: Optional[str] = None
    post_id: Optional[int] = None
    post_tags_match: Optional[str] = None
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    is_deleted: Optional[bool] = None
    is_sticky: Optional[bool] = None
    do_not_bump_post: Optional[bool] = None
    
    def to_params(self, prefix: str = "search") -> Dict[str, Any]:
        params = super().to_params(prefix)
        
        if self.body_matches:
            params[f"{prefix}[body_matches]"] = self.body_matches
        if self.post_id:
            params[f"{prefix}[post_id]"] = self.post_id
        if self.post_tags_match:
            params[f"{prefix}[post_tags_match]"] = self.post_tags_match
        if self.creator_id:
            params[f"{prefix}[creator_id]"] = self.creator_id
        if self.creator_name:
            params[f"{prefix}[creator_name]"] = self.creator_name
        if self.is_deleted is not None:
            params[f"{prefix}[is_deleted]"] = str(self.is_deleted).lower()
        if self.is_sticky is not None:
            params[f"{prefix}[is_sticky]"] = str(self.is_sticky).lower()
        if self.do_not_bump_post is not None:
            params[f"{prefix}[do_not_bump_post]"] = str(self.do_not_bump_post).lower()
        
        return params