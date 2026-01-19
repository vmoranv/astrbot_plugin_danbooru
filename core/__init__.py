"""
Danbooru API Plugin - Core Module
核心模块：提供HTTP客户端、认证、配置管理和基础设施
"""

from .client import DanbooruClient
from .auth import AuthManager
from .config import PluginConfig
from .exceptions import (
    DanbooruError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ForbiddenError,
    ValidationError,
    APIError,
)
from .models import (
    PaginationParams,
    SearchParams,
    APIResponse,
)

__all__ = [
    # Client
    "DanbooruClient",
    # Auth
    "AuthManager",
    # Config
    "PluginConfig",
    # Exceptions
    "DanbooruError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ForbiddenError",
    "ValidationError",
    "APIError",
    # Models
    "PaginationParams",
    "SearchParams",
    "APIResponse",
]