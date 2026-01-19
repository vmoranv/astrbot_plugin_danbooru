"""
Danbooru API Plugin - Tag 数据模型
定义标签相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .base import SearchParams, TagCategory


@dataclass
class Tag:
    """标签模型"""
    id: int
    name: str
    post_count: int = 0
    category: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_deprecated: bool = False
    words: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """从字典创建实例"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TagSearchParams(SearchParams):
    """标签搜索参数"""
    name_matches: Optional[str] = None  # 支持通配符
    category: Optional[TagCategory] = None
    hide_empty: Optional[bool] = None
    has_wiki: Optional[bool] = None
    has_artist: Optional[bool] = None
    is_deprecated: Optional[bool] = None
    
    def to_params(self, prefix: str = "search") -> Dict[str, Any]:
        params = super().to_params(prefix)
        
        if self.name_matches:
            params[f"{prefix}[name_matches]"] = self.name_matches
        
        if self.category:
            params[f"{prefix}[category]"] = self.category.value if isinstance(self.category, TagCategory) else self.category
        
        if self.hide_empty is not None:
            params[f"{prefix}[hide_empty]"] = str(self.hide_empty).lower()
        
        if self.has_wiki is not None:
            params[f"{prefix}[has_wiki]"] = str(self.has_wiki).lower()
        
        if self.has_artist is not None:
            params[f"{prefix}[has_artist]"] = str(self.has_artist).lower()
        
        if self.is_deprecated is not None:
            params[f"{prefix}[is_deprecated]"] = str(self.is_deprecated).lower()
        
        return params


@dataclass
class RelatedTag:
    """相关标签模型"""
    tag: str
    category: int = 0
    post_count: int = 0
    frequency: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelatedTag':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TagAlias:
    """标签别名模型"""
    id: int
    antecedent_name: str
    consequent_name: str
    status: str = "active"
    creator_id: Optional[int] = None
    approver_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TagAlias':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TagImplication:
    """标签蕴含模型"""
    id: int
    antecedent_name: str
    consequent_name: str
    status: str = "active"
    creator_id: Optional[int] = None
    approver_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TagImplication':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})