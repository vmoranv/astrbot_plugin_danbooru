"""
Danbooru API Plugin - Upload 数据模型
定义上传相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Upload:
    """上传模型"""
    id: int
    uploader_id: int
    source: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None
    post_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Upload':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})