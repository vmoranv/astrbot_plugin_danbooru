"""
Danbooru API Plugin - Artist 数据模型
定义艺术家相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .base import SearchParams


@dataclass
class Artist:
    """艺术家模型"""
    id: int
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    creator_id: Optional[int] = None
    is_active: bool = True
    is_banned: bool = False
    is_deleted: bool = False
    group_name: Optional[str] = None
    other_names: Optional[List[str]] = None
    urls: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Artist':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ArtistSearchParams(SearchParams):
    """艺术家搜索参数"""
    name: Optional[str] = None
    name_matches: Optional[str] = None
    group_name: Optional[str] = None
    any_other_name_matches: Optional[str] = None
    any_name_matches: Optional[str] = None
    url_matches: Optional[str] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    is_deleted: Optional[bool] = None
    has_tag: Optional[bool] = None
    
    def to_params(self, prefix: str = "search") -> Dict[str, Any]:
        params = super().to_params(prefix)
        
        if self.name:
            params[f"{prefix}[name]"] = self.name
        if self.name_matches:
            params[f"{prefix}[name_matches]"] = self.name_matches
        if self.group_name:
            params[f"{prefix}[group_name]"] = self.group_name
        if self.any_other_name_matches:
            params[f"{prefix}[any_other_name_matches]"] = self.any_other_name_matches
        if self.any_name_matches:
            params[f"{prefix}[any_name_matches]"] = self.any_name_matches
        if self.url_matches:
            params[f"{prefix}[url_matches]"] = self.url_matches
        if self.is_active is not None:
            params[f"{prefix}[is_active]"] = str(self.is_active).lower()
        if self.is_banned is not None:
            params[f"{prefix}[is_banned]"] = str(self.is_banned).lower()
        if self.is_deleted is not None:
            params[f"{prefix}[is_deleted]"] = str(self.is_deleted).lower()
        if self.has_tag is not None:
            params[f"{prefix}[has_tag]"] = str(self.has_tag).lower()
        
        return params


@dataclass
class ArtistCommentary:
    """艺术家评注模型"""
    id: int
    post_id: int
    original_title: Optional[str] = None
    original_description: Optional[str] = None
    translated_title: Optional[str] = None
    translated_description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArtistCommentary':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})