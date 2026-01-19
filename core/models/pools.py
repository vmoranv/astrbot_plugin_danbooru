"""
Danbooru API Plugin - Pool 数据模型
定义图池相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .base import SearchParams


@dataclass
class Pool:
    """图池模型"""
    id: int
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    creator_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    category: Optional[str] = None
    post_ids: Optional[List[int]] = None
    post_count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pool':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass 
class PoolSearchParams(SearchParams):
    """图池搜索参数"""
    name_matches: Optional[str] = None
    description_matches: Optional[str] = None
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None
    category: Optional[str] = None
    
    def to_params(self, prefix: str = "search") -> Dict[str, Any]:
        params = super().to_params(prefix)
        
        if self.name_matches:
            params[f"{prefix}[name_matches]"] = self.name_matches
        if self.description_matches:
            params[f"{prefix}[description_matches]"] = self.description_matches
        if self.creator_id:
            params[f"{prefix}[creator_id]"] = self.creator_id
        if self.creator_name:
            params[f"{prefix}[creator_name]"] = self.creator_name
        if self.is_active is not None:
            params[f"{prefix}[is_active]"] = str(self.is_active).lower()
        if self.is_deleted is not None:
            params[f"{prefix}[is_deleted]"] = str(self.is_deleted).lower()
        if self.category:
            params[f"{prefix}[category]"] = self.category
        
        return params