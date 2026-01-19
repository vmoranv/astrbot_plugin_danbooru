"""
Danbooru API Plugin - User 数据模型
定义用户相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .base import SearchParams


@dataclass
class User:
    """用户模型"""
    id: int
    name: str
    level: int = 0
    level_string: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    post_upload_count: int = 0
    post_update_count: int = 0
    note_update_count: int = 0
    is_banned: bool = False
    is_deleted: bool = False
    can_approve_posts: bool = False
    can_upload_free: bool = False
    inviter_id: Optional[int] = None
    favorite_count: int = 0
    comment_count: int = 0
    forum_post_count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class UserSearchParams(SearchParams):
    """用户搜索参数"""
    name: Optional[str] = None
    name_matches: Optional[str] = None
    level: Optional[int] = None
    min_level: Optional[int] = None
    max_level: Optional[int] = None
    is_banned: Optional[bool] = None
    is_deleted: Optional[bool] = None
    can_approve_posts: Optional[bool] = None
    can_upload_free: Optional[bool] = None
    
    def to_params(self, prefix: str = "search") -> Dict[str, Any]:
        params = super().to_params(prefix)
        
        if self.name:
            params[f"{prefix}[name]"] = self.name
        if self.name_matches:
            params[f"{prefix}[name_matches]"] = self.name_matches
        if self.level is not None:
            params[f"{prefix}[level]"] = self.level
        if self.min_level is not None:
            params[f"{prefix}[min_level]"] = self.min_level
        if self.max_level is not None:
            params[f"{prefix}[max_level]"] = self.max_level
        if self.is_banned is not None:
            params[f"{prefix}[is_banned]"] = str(self.is_banned).lower()
        if self.is_deleted is not None:
            params[f"{prefix}[is_deleted]"] = str(self.is_deleted).lower()
        if self.can_approve_posts is not None:
            params[f"{prefix}[can_approve_posts]"] = str(self.can_approve_posts).lower()
        if self.can_upload_free is not None:
            params[f"{prefix}[can_upload_free]"] = str(self.can_upload_free).lower()
        
        return params