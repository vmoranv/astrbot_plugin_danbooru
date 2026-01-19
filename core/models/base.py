"""
Danbooru API Plugin - 基础数据模型
定义枚举、分页、搜索参数和API响应的通用结构
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Generic, TypeVar, Union
from enum import Enum
from datetime import datetime
import json


T = TypeVar('T')


class Rating(Enum):
    """图片分级"""
    GENERAL = "g"
    SENSITIVE = "s"
    QUESTIONABLE = "q"
    EXPLICIT = "e"


class TagCategory(Enum):
    """标签类别"""
    GENERAL = 0
    ARTIST = 1
    COPYRIGHT = 3
    CHARACTER = 4
    META = 5


class PostStatus(Enum):
    """帖子状态"""
    ACTIVE = "active"
    PENDING = "pending"
    DELETED = "deleted"
    FLAGGED = "flagged"
    BANNED = "banned"


class OrderDirection(Enum):
    """排序方向"""
    ASC = "asc"
    DESC = "desc"


@dataclass
class PaginationParams:
    """分页参数"""
    page: Optional[int] = None
    limit: Optional[int] = None
    before_id: Optional[int] = None  # b<id>
    after_id: Optional[int] = None   # a<id>
    
    def to_params(self) -> Dict[str, Any]:
        """转换为API参数"""
        params = {}
        if self.limit is not None:
            params["limit"] = min(self.limit, 200)  # 最大200
        
        if self.before_id is not None:
            params["page"] = f"b{self.before_id}"
        elif self.after_id is not None:
            params["page"] = f"a{self.after_id}"
        elif self.page is not None:
            params["page"] = self.page
        
        return params


@dataclass
class SearchParams:
    """通用搜索参数"""
    id: Optional[Union[int, List[int], str]] = None  # 支持范围和列表
    created_at: Optional[str] = None  # 日期范围
    updated_at: Optional[str] = None
    order: Optional[str] = None
    
    def to_params(self, prefix: str = "search") -> Dict[str, Any]:
        """转换为API参数"""
        params = {}
        
        if self.id is not None:
            if isinstance(self.id, list):
                params[f"{prefix}[id]"] = ",".join(map(str, self.id))
            else:
                params[f"{prefix}[id]"] = self.id
        
        if self.created_at is not None:
            params[f"{prefix}[created_at]"] = self.created_at
        
        if self.updated_at is not None:
            params[f"{prefix}[updated_at]"] = self.updated_at
        
        if self.order is not None:
            params[f"{prefix}[order]"] = self.order
        
        return params


@dataclass
class RateLimitInfo:
    """速率限制信息"""
    limit: int
    remaining: int
    reset_at: Optional[datetime] = None
    burst_pool: Optional[int] = None
    recharge_rate: Optional[float] = None
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> Optional['RateLimitInfo']:
        """从响应头解析速率限制信息"""
        rate_limit_header = headers.get("x-rate-limit")
        if not rate_limit_header:
            return None
        
        try:
            data = json.loads(rate_limit_header)
            return cls(
                limit=data.get("limit", 0),
                remaining=data.get("remaining", 0),
                burst_pool=data.get("burst_pool"),
                recharge_rate=data.get("recharge_rate"),
            )
        except (json.JSONDecodeError, KeyError):
            return None


@dataclass
class APIResponse(Generic[T]):
    """API响应封装"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    rate_limit: Optional[RateLimitInfo] = None
    
    @classmethod
    def success_response(cls, data: T, status_code: int = 200, headers: Dict[str, str] = None) -> 'APIResponse[T]':
        """创建成功响应"""
        return cls(
            success=True,
            data=data,
            status_code=status_code,
            headers=headers or {},
        )
    
    @classmethod
    def error_response(cls, error: str, status_code: int = 400) -> 'APIResponse[T]':
        """创建错误响应"""
        return cls(
            success=False,
            error=error,
            status_code=status_code,
        )