"""
Danbooru API Plugin - Version 数据模型
定义版本历史相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class PostVersion:
    """帖子版本模型"""
    id: int
    post_id: int
    updater_id: int
    tags: Optional[str] = None
    added_tags: Optional[List[str]] = None
    removed_tags: Optional[List[str]] = None
    rating: Optional[str] = None
    rating_changed: bool = False
    parent_id: Optional[int] = None
    parent_changed: bool = False
    source: Optional[str] = None
    source_changed: bool = False
    version: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PostVersion':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})