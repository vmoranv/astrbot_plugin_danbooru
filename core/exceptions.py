"""
Danbooru API Plugin - 异常定义模块
定义所有API相关的自定义异常
"""

from typing import Optional, Dict, Any


class DanbooruError(Exception):
    """Danbooru API 基础异常类"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "response_data": self.response_data,
        }


class APIError(DanbooruError):
    """通用API错误"""
    pass


class AuthenticationError(DanbooruError):
    """认证错误 - HTTP 401"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=401, response_data=response_data)


class ForbiddenError(DanbooruError):
    """权限不足错误 - HTTP 403"""
    
    def __init__(
        self,
        message: str = "Access denied",
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=403, response_data=response_data)


class NotFoundError(DanbooruError):
    """资源未找到错误 - HTTP 404"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=404, response_data=response_data)


class RateLimitError(DanbooruError):
    """速率限制错误 - HTTP 429"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        response_data: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, status_code=429, response_data=response_data)
        self.retry_after = retry_after


class ValidationError(DanbooruError):
    """参数验证错误 - HTTP 422/424"""
    
    def __init__(
        self,
        message: str = "Invalid parameters",
        status_code: int = 422,
        response_data: Optional[Dict[str, Any]] = None,
        field_errors: Optional[Dict[str, str]] = None,
    ):
        super().__init__(message, status_code=status_code, response_data=response_data)
        self.field_errors = field_errors or {}


class ResourceLockedError(DanbooruError):
    """资源锁定错误 - HTTP 422"""
    
    def __init__(
        self,
        message: str = "Resource is locked",
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=422, response_data=response_data)


class ResourceExistsError(DanbooruError):
    """资源已存在错误 - HTTP 423"""
    
    def __init__(
        self,
        message: str = "Resource already exists",
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=423, response_data=response_data)


class PaginationLimitError(DanbooruError):
    """分页限制错误 - HTTP 410"""
    
    def __init__(
        self,
        message: str = "Pagination limit exceeded",
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=410, response_data=response_data)


class ServerError(DanbooruError):
    """服务器内部错误 - HTTP 5xx"""
    
    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = 500,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=status_code, response_data=response_data)


class ServiceUnavailableError(DanbooruError):
    """服务不可用错误 - HTTP 502/503"""
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        status_code: int = 503,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=status_code, response_data=response_data)


class ConfigurationError(DanbooruError):
    """配置错误"""
    
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status_code=None)


class EventError(DanbooruError):
    """事件处理错误"""
    
    def __init__(self, message: str = "Event processing error"):
        super().__init__(message, status_code=None)


# HTTP状态码到异常类的映射
STATUS_CODE_EXCEPTIONS = {
    400: ValidationError,
    401: AuthenticationError,
    403: ForbiddenError,
    404: NotFoundError,
    410: PaginationLimitError,
    420: ValidationError,  # Invalid Record
    422: ResourceLockedError,
    423: ResourceExistsError,
    424: ValidationError,  # Invalid Parameters
    429: RateLimitError,
    500: ServerError,
    502: ServiceUnavailableError,
    503: ServiceUnavailableError,
}


def raise_for_status(status_code: int, message: str = "", response_data: Optional[Dict[str, Any]] = None):
    """根据HTTP状态码抛出相应的异常"""
    if status_code < 400:
        return
    
    exception_class = STATUS_CODE_EXCEPTIONS.get(status_code, APIError)
    
    if exception_class == ValidationError and status_code in (420, 424):
        raise exception_class(message or "Validation failed", status_code=status_code, response_data=response_data)
    elif exception_class in (ServerError, ServiceUnavailableError):
        raise exception_class(message or "Server error", status_code=status_code, response_data=response_data)
    else:
        raise exception_class(message or "API error", response_data=response_data)