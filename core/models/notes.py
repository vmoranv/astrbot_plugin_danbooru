"""
Danbooru API Plugin - Note 数据模型
定义注释相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .base import SearchParams


@dataclass
class Note:
    """注释模型"""
    id: int
    post_id: int
    creator_id: int
    x: int
    y: int
    width: int
    height: int
    body: str
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: int = 1
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NoteSearchParams(SearchParams):
    """注释搜索参数"""
    body_matches: Optional[str] = None
    post_id: Optional[int] = None
    post_tags_match: Optional[str] = None
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    is_active: Optional[bool] = None
    
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
        if self.is_active is not None:
            params[f"{prefix}[is_active]"] = str(self.is_active).lower()
        
        return params