"""
Danbooru API Plugin - HTTP客户端模块
核心HTTP客户端，处理所有API请求
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, TypeVar
import time
from urllib.parse import urlparse

from astrbot.api import logger

from .auth import AuthManager
from .config import PluginConfig
from .exceptions import (
    DanbooruError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ServerError,
    ServiceUnavailableError,
    raise_for_status,
)
from .models import APIResponse, RateLimitInfo
from .http_utils import RequestOptions, RateLimiter, ResponseCache
from ..events.event_bus import EventBus
from ..events.event_types import APIRequestEvent, APIResponseEvent, ErrorEvent


T = TypeVar('T')




class DanbooruClient:
    """Danbooru API 客户端"""

    _sensitive_keys = {
        "password",
        "old_password",
        "new_password",
        "password_confirmation",
        "api_key",
        "login",
        "token",
    }
    
    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        auth_manager: Optional[AuthManager] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.config = config or PluginConfig()
        self.auth = auth_manager or AuthManager(
            username=self.config.auth.username,
            api_key=self.config.auth.api_key,
        )
        self.event_bus = event_bus
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._http_proxy: Optional[str] = None
        self._rate_limiter = RateLimiter(self.config.api.rate_limit_per_second)
        self._cache = ResponseCache(
            max_size=self.config.cache.max_size,
            default_ttl=self.config.cache.ttl_seconds,
        )
        
        self._request_count = 0
        self._last_rate_limit_info: Optional[RateLimitInfo] = None
    
    @property
    def base_url(self) -> str:
        """获取API基础URL"""
        return self.config.api.active_url
    
    @property
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self.auth.is_authenticated
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.api.timeout)
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            self._http_proxy = None
            proxy_url = self.config.proxy.build_url()
            if proxy_url:
                scheme = urlparse(proxy_url).scheme.lower()
                if scheme.startswith("socks"):
                    try:
                        from aiohttp_socks import ProxyConnector
                    except ImportError:
                        logger.warning(
                            "代理协议为 SOCKS，但未安装 aiohttp-socks，将忽略代理设置"
                        )
                    else:
                        connector = ProxyConnector.from_url(proxy_url)
                else:
                    self._http_proxy = proxy_url
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "User-Agent": "AstrBot-Danbooru-Plugin/1.0",
                    "Accept": "application/json",
                },
            )
        return self._session
    
    async def close(self) -> None:
        """关闭客户端"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self) -> 'DanbooruClient':
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        await self.close()

    def _sanitize_payload(self, data: Any) -> Any:
        """遮蔽敏感字段，避免在事件中泄露凭证"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if key in self._sensitive_keys:
                    sanitized[key] = "***"
                else:
                    sanitized[key] = self._sanitize_payload(value)
            return sanitized
        if isinstance(data, list):
            return [self._sanitize_payload(item) for item in data]
        return data

    async def _emit_event(self, event) -> None:
        """发送事件（如启用事件总线）"""
        if self.event_bus:
            await self.event_bus.emit(event)
    
    def _build_url(self, endpoint: str, format: str = "json") -> str:
        """构建完整URL"""
        # 移除开头的斜杠
        endpoint = endpoint.lstrip("/")
        
        # 添加格式后缀
        if not endpoint.endswith(f".{format}"):
            if "." in endpoint.split("/")[-1]:
                # 已经有格式后缀
                pass
            else:
                endpoint = f"{endpoint}.{format}"
        
        return f"{self.base_url}/{endpoint}"
    
    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        response_format: str = "json"
    ) -> APIResponse:
        """处理响应"""
        status = response.status
        headers = dict(response.headers)
        
        # 解析速率限制信息
        rate_limit_info = RateLimitInfo.from_headers(headers)
        if rate_limit_info:
            self._last_rate_limit_info = rate_limit_info
        
        # 读取响应体
        try:
            if response_format == "json":
                data = await response.json()
            else:
                data = await response.text()
        except (json.JSONDecodeError, aiohttp.ContentTypeError):
            data = await response.text()
        
        # 检查错误状态
        if status >= 400:
            error_message = ""
            if isinstance(data, dict):
                error_message = data.get("message") or data.get("reason") or str(data)
            else:
                error_message = str(data)
            
            raise_for_status(status, error_message, data if isinstance(data, dict) else None)
        
        return APIResponse(
            success=True,
            data=data,
            status_code=status,
            headers=headers,
            rate_limit=rate_limit_info,
        )
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        use_cache: bool = True,
    ) -> APIResponse:
        """
        发送API请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            data: 表单数据
            json_data: JSON数据
            options: 请求选项
            use_cache: 是否使用缓存（仅GET请求）
        
        Returns:
            APIResponse对象
        """
        options = options or RequestOptions()
        response_format = options.response_format
        start_time = time.time()

        raw_params = params or {}
        event_params = self._sanitize_payload(raw_params)
        event_body = self._sanitize_payload(json_data if json_data is not None else data)

        await self._emit_event(APIRequestEvent(
            method=method.upper(),
            endpoint=endpoint,
            params=event_params,
            body=event_body,
        ))

        if self.config.log_api_calls:
            logger.info(
                f"[danbooru] {method.upper()} {endpoint} "
                f"params={event_params} body={event_body} cache={use_cache}"
            )
        elif self.config.debug:
            logger.debug(
                f"[danbooru] {method.upper()} {endpoint} "
                f"params={event_params} body={event_body} cache={use_cache}"
            )
        
        # 构建URL
        url = self._build_url(endpoint, response_format)
        
        # 准备参数
        params = dict(raw_params)
        headers = {}
        
        # 应用认证
        if options.use_auth and self.is_authenticated:
            headers, params = self.auth.apply_auth(
                headers, params, method=options.auth_method
            )
        
        # 检查缓存（仅GET请求）
        if use_cache and method.upper() == "GET" and self.config.cache.enabled:
            cached = await self._cache.get(method, url, params)
            if cached is not None:
                duration_ms = (time.time() - start_time) * 1000
                await self._emit_event(APIResponseEvent(
                    method=method.upper(),
                    endpoint=endpoint,
                    status_code=200,
                    response_data=self._sanitize_payload(cached),
                    duration_ms=duration_ms,
                    from_cache=True,
                ))
                if self.config.log_api_calls:
                    logger.info(
                        f"[danbooru] {method.upper()} {endpoint} -> 200 "
                        f"cache hit ({duration_ms:.1f}ms)"
                    )
                elif self.config.debug:
                    logger.debug(
                        f"[danbooru] {method.upper()} {endpoint} -> 200 "
                        f"cache hit ({duration_ms:.1f}ms)"
                    )
                return APIResponse.success_response(cached)
        
        # 速率限制
        await self._rate_limiter.acquire()
        
        # 重试逻辑
        max_retries = options.retries or self.config.api.max_retries
        last_error: Optional[Exception] = None
        
        for attempt in range(max_retries + 1):
            try:
                session = await self._get_session()
                
                # 发送请求
                async with session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=headers,
                    proxy=self._http_proxy,
                ) as response:
                    self._request_count += 1
                    result = await self._handle_response(response, response_format)
                    
                    # 缓存结果
                    if (
                        use_cache 
                        and method.upper() == "GET" 
                        and self.config.cache.enabled 
                        and result.success
                    ):
                        await self._cache.set(method, url, result.data, params)

                    duration_ms = (time.time() - start_time) * 1000
                    await self._emit_event(APIResponseEvent(
                        method=method.upper(),
                        endpoint=endpoint,
                        status_code=result.status_code,
                        response_data=self._sanitize_payload(result.data),
                        duration_ms=duration_ms,
                        from_cache=False,
                    ))
                    if self.config.log_api_calls:
                        logger.info(
                            f"[danbooru] {method.upper()} {endpoint} -> {result.status_code} "
                            f"({duration_ms:.1f}ms)"
                        )
                    elif self.config.debug:
                        logger.debug(
                            f"[danbooru] {method.upper()} {endpoint} -> {result.status_code} "
                            f"({duration_ms:.1f}ms)"
                        )

                    return result
                    
            except RateLimitError as e:
                last_error = e
                if e.retry_after:
                    await asyncio.sleep(e.retry_after)
                else:
                    await asyncio.sleep(self.config.api.retry_delay * (2 ** attempt))
                    
            except (ServiceUnavailableError, ServerError) as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(self.config.api.retry_delay * (2 ** attempt))
                    
            except aiohttp.ClientError as e:
                last_error = DanbooruError(f"网络请求失败: {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(self.config.api.retry_delay)
        
        # 所有重试都失败
        if last_error:
            duration_ms = (time.time() - start_time) * 1000
            error_type = "api"
            if isinstance(last_error, AuthenticationError):
                error_type = "auth"
            elif isinstance(last_error, RateLimitError):
                error_type = "rate_limit"
            elif isinstance(last_error, ValidationError):
                error_type = "validation"
            elif isinstance(last_error, DanbooruError):
                error_type = "api"
            elif isinstance(last_error, aiohttp.ClientError):
                error_type = "network"

            await self._emit_event(ErrorEvent(
                error_type=error_type,
                error_message=str(last_error),
                error_code=getattr(last_error, "status_code", None),
                original_event={
                    "method": method.upper(),
                    "endpoint": endpoint,
                    "params": event_params,
                },
            ))
            if self.config.log_api_calls:
                logger.info(
                    f"[danbooru] {method.upper()} {endpoint} -> error "
                    f"{error_type} ({duration_ms:.1f}ms)"
                )
            elif self.config.debug:
                logger.debug(
                    f"[danbooru] {method.upper()} {endpoint} -> error "
                    f"{error_type} ({duration_ms:.1f}ms)"
                )
            raise last_error
        raise DanbooruError("请求失败，未知错误")
    
    # ==================== 便捷方法 ====================
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """GET请求"""
        return await self.request("GET", endpoint, params=params, **kwargs)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """POST请求"""
        return await self.request("POST", endpoint, data=data, json_data=json_data, **kwargs)
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """PUT请求"""
        return await self.request("PUT", endpoint, data=data, json_data=json_data, **kwargs)
    
    async def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """PATCH请求"""
        return await self.request("PATCH", endpoint, data=data, json_data=json_data, **kwargs)
    
    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """DELETE请求"""
        return await self.request("DELETE", endpoint, params=params, **kwargs)
    
    # ==================== 缓存管理 ====================
    
    async def clear_cache(self) -> None:
        """清空缓存"""
        await self._cache.clear()
    
    async def invalidate_cache(self, pattern: str = "") -> int:
        """使缓存失效"""
        return await self._cache.invalidate(pattern)
    
    # ==================== 状态信息 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "request_count": self._request_count,
            "is_authenticated": self.is_authenticated,
            "base_url": self.base_url,
            "rate_limit": self._last_rate_limit_info.__dict__ if self._last_rate_limit_info else None,
        }
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.get("/status", use_cache=False)
            return response.success
        except Exception:
            return False
    
    async def get_profile(self) -> APIResponse:
        """获取当前用户信息"""
        if not self.is_authenticated:
            raise AuthenticationError("需要认证才能获取个人信息")
        
        return await self.get("/profile")
