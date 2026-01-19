"""
Danbooru API Plugin - Post 数据模型
定义帖子相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .base import SearchParams, Rating, PostStatus


@dataclass
class Post:
    """帖子模型"""
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    uploader_id: Optional[int] = None
    approver_id: Optional[int] = None
    tag_string: Optional[str] = None
    tag_string_general: Optional[str] = None
    tag_string_character: Optional[str] = None
    tag_string_copyright: Optional[str] = None
    tag_string_artist: Optional[str] = None
    tag_string_meta: Optional[str] = None
    rating: Optional[str] = None
    parent_id: Optional[int] = None
    source: Optional[str] = None
    md5: Optional[str] = None
    file_url: Optional[str] = None
    large_file_url: Optional[str] = None
    preview_file_url: Optional[str] = None
    file_ext: Optional[str] = None
    file_size: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    score: Optional[int] = None
    up_score: Optional[int] = None
    down_score: Optional[int] = None
    fav_count: Optional[int] = None
    has_children: bool = False
    is_pending: bool = False
    is_flagged: bool = False
    is_deleted: bool = False
    is_banned: bool = False
    pixiv_id: Optional[int] = None
    last_commented_at: Optional[str] = None
    has_active_children: bool = False
    bit_flags: Optional[int] = None
    tag_count: Optional[int] = None
    tag_count_general: Optional[int] = None
    tag_count_artist: Optional[int] = None
    tag_count_character: Optional[int] = None
    tag_count_copyright: Optional[int] = None
    tag_count_meta: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Post':
        """从字典创建实例"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class PostSearchParams(SearchParams):
    """帖子搜索参数"""
    tags: Optional[str] = None
    rating: Optional[Rating] = None
    score: Optional[str] = None  # 支持范围
    uploader_id: Optional[int] = None
    approver_id: Optional[int] = None
    parent_id: Optional[int] = None
    source: Optional[str] = None
    md5: Optional[str] = None
    status: Optional[PostStatus] = None
    has_children: Optional[bool] = None
    is_pending: Optional[bool] = None
    is_flagged: Optional[bool] = None
    is_deleted: Optional[bool] = None
    is_banned: Optional[bool] = None
    filetype: Optional[str] = None
    
    def to_params(self, prefix: str = "search") -> Dict[str, Any]:
        """转换为API参数"""
        params = super().to_params(prefix)
        
        if self.tags:
            params["tags"] = self.tags
        
        if self.rating:
            params[f"{prefix}[rating]"] = self.rating.value if isinstance(self.rating, Rating) else self.rating
        
        if self.score:
            params[f"{prefix}[score]"] = self.score
        
        if self.uploader_id:
            params[f"{prefix}[uploader_id]"] = self.uploader_id
        
        if self.approver_id:
            params[f"{prefix}[approver_id]"] = self.approver_id
        
        if self.parent_id:
            params[f"{prefix}[parent_id]"] = self.parent_id
        
        if self.source:
            params[f"{prefix}[source]"] = self.source
        
        if self.md5:
            params[f"{prefix}[md5]"] = self.md5
        
        if self.status:
            params[f"{prefix}[status]"] = self.status.value if isinstance(self.status, PostStatus) else self.status
        
        if self.has_children is not None:
            params[f"{prefix}[has_children]"] = str(self.has_children).lower()
        
        if self.is_pending is not None:
            params[f"{prefix}[is_pending]"] = str(self.is_pending).lower()
        
        if self.is_flagged is not None:
            params[f"{prefix}[is_flagged]"] = str(self.is_flagged).lower()
        
        if self.is_deleted is not None:
            params[f"{prefix}[is_deleted]"] = str(self.is_deleted).lower()
        
        if self.is_banned is not None:
            params[f"{prefix}[is_banned]"] = str(self.is_banned).lower()
        
        if self.filetype:
            params[f"{prefix}[filetype]"] = self.filetype
        
        return params