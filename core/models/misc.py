"""
Danbooru API Plugin - Misc 数据模型
定义杂项相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class Dmail:
    """私信模型"""
    id: int
    owner_id: int
    from_id: int
    to_id: int
    title: str
    body: str
    is_read: bool = False
    is_deleted: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dmail':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SavedSearch:
    """保存的搜索模型"""
    id: int
    user_id: int
    query: str
    labels: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SavedSearch':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class IPAddress:
    """IP地址模型"""
    ip_addr: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IPAddress':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})