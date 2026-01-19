"""
Danbooru API Plugin - Favorite 数据模型
定义收藏相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class Favorite:
    """收藏模型"""
    id: int
    post_id: int
    user_id: int
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Favorite':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class FavoriteGroup:
    """收藏组模型"""
    id: int
    name: str
    creator_id: int
    post_ids: Optional[List[int]] = None
    post_count: int = 0
    is_public: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FavoriteGroup':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})