"""
Danbooru API Plugin - Wiki 数据模型
定义Wiki页面相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .base import SearchParams


@dataclass
class WikiPage:
    """Wiki页面模型"""
    id: int
    title: str
    body: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    creator_id: Optional[int] = None
    updater_id: Optional[int] = None
    is_locked: bool = False
    is_deleted: bool = False
    other_names: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WikiPage':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class WikiSearchParams(SearchParams):
    """Wiki搜索参数"""
    title: Optional[str] = None
    title_matches: Optional[str] = None
    body_matches: Optional[str] = None
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    is_locked: Optional[bool] = None
    is_deleted: Optional[bool] = None
    other_names_match: Optional[str] = None
    hide_deleted: Optional[bool] = None
    
    def to_params(self, prefix: str = "search") -> Dict[str, Any]:
        params = super().to_params(prefix)
        
        if self.title:
            params[f"{prefix}[title]"] = self.title
        if self.title_matches:
            params[f"{prefix}[title_matches]"] = self.title_matches
        if self.body_matches:
            params[f"{prefix}[body_matches]"] = self.body_matches
        if self.creator_id:
            params[f"{prefix}[creator_id]"] = self.creator_id
        if self.creator_name:
            params[f"{prefix}[creator_name]"] = self.creator_name
        if self.is_locked is not None:
            params[f"{prefix}[is_locked]"] = str(self.is_locked).lower()
        if self.is_deleted is not None:
            params[f"{prefix}[is_deleted]"] = str(self.is_deleted).lower()
        if self.other_names_match:
            params[f"{prefix}[other_names_match]"] = self.other_names_match
        if self.hide_deleted is not None:
            params[f"{prefix}[hide_deleted]"] = str(self.hide_deleted).lower()
        
        return params