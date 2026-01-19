"""
Danbooru API Plugin - Forum 数据模型
定义论坛相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ForumTopic:
    """论坛主题模型"""
    id: int
    title: str
    creator_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_sticky: bool = False
    is_locked: bool = False
    is_deleted: bool = False
    category_id: int = 0
    response_count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForumTopic':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ForumPost:
    """论坛帖子模型"""
    id: int
    topic_id: int
    creator_id: int
    body: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_deleted: bool = False
    updater_id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForumPost':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})