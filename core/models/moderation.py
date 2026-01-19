"""
Danbooru API Plugin - Moderation 数据模型
定义审核相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class PostFlag:
    """帖子标记模型"""
    id: int
    post_id: int
    creator_id: int
    reason: str
    is_resolved: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PostFlag':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PostAppeal:
    """帖子申诉模型"""
    id: int
    post_id: int
    creator_id: int
    reason: str
    status: str = "pending"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PostAppeal':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Ban:
    """封禁模型"""
    id: int
    user_id: int
    banner_id: int
    reason: str
    expires_at: Optional[str] = None
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ban':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ModAction:
    """管理员操作模型"""
    id: int
    creator_id: int
    category: str
    description: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModAction':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class BulkUpdateRequest:
    """批量更新请求模型"""
    id: int
    creator_id: int
    approver_id: Optional[int] = None
    script: str = ""
    title: str = ""
    status: str = "pending"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BulkUpdateRequest':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})