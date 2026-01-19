"""
Danbooru API Plugin - 服务基类
所有API服务的抽象基类
"""

from abc import ABC
from typing import Optional, Dict, Any, TypeVar

from ..core.client import DanbooruClient
from ..core.models import PaginationParams, APIResponse
from ..events.event_bus import EventBus, Event


T = TypeVar('T')


class BaseService(ABC):
    """API服务基类"""
    
    # 子类需要定义的端点前缀
    _endpoint_prefix: str = ""
    
    def __init__(self, client: DanbooruClient, event_bus: Optional[EventBus] = None):
        """
        初始化服务
        
        Args:
            client: Danbooru API客户端
            event_bus: 事件总线（可选）
        """
        self.client = client
        self.event_bus = event_bus or EventBus.get_instance()
    
    @property
    def endpoint(self) -> str:
        """获取端点前缀"""
        return self._endpoint_prefix
    
    def _build_endpoint(self, *parts: str) -> str:
        """构建完整端点路径"""
        path_parts = [self._endpoint_prefix] if self._endpoint_prefix else []
        path_parts.extend(str(p) for p in parts if p)
        return "/".join(path_parts)
    
    async def _emit_event(self, event: Event) -> None:
        """发送事件"""
        if self.event_bus:
            await self.event_bus.emit(event)
    
    def _apply_pagination(
        self, 
        params: Dict[str, Any], 
        pagination: Optional[PaginationParams] = None
    ) -> Dict[str, Any]:
        """应用分页参数"""
        if pagination:
            params.update(pagination.to_params())
        return params
    
    async def _list(
        self,
        endpoint: str = "",
        params: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        列表查询
        
        Args:
            endpoint: 端点路径
            params: 查询参数
            pagination: 分页参数
        
        Returns:
            API响应
        """
        full_endpoint = self._build_endpoint(endpoint) if endpoint else self._endpoint_prefix
        query_params = self._apply_pagination(params or {}, pagination)
        return await self.client.get(full_endpoint, params=query_params)
    
    async def _get(
        self,
        resource_id: int,
        endpoint: str = "",
    ) -> APIResponse:
        """
        获取单个资源
        
        Args:
            resource_id: 资源ID
            endpoint: 端点路径
        
        Returns:
            API响应
        """
        full_endpoint = self._build_endpoint(endpoint, str(resource_id))
        return await self.client.get(full_endpoint)
    
    async def _create(
        self,
        data: Dict[str, Any],
        endpoint: str = "",
    ) -> APIResponse:
        """
        创建资源
        
        Args:
            data: 资源数据
            endpoint: 端点路径
        
        Returns:
            API响应
        """
        full_endpoint = self._build_endpoint(endpoint) if endpoint else self._endpoint_prefix
        return await self.client.post(full_endpoint, json_data=data)
    
    async def _update(
        self,
        resource_id: int,
        data: Dict[str, Any],
        endpoint: str = "",
        method: str = "PUT",
    ) -> APIResponse:
        """
        更新资源
        
        Args:
            resource_id: 资源ID
            data: 更新数据
            endpoint: 端点路径
            method: HTTP方法（PUT或PATCH）
        
        Returns:
            API响应
        """
        full_endpoint = self._build_endpoint(endpoint, str(resource_id))
        if method.upper() == "PATCH":
            return await self.client.patch(full_endpoint, json_data=data)
        return await self.client.put(full_endpoint, json_data=data)
    
    async def _delete(
        self,
        resource_id: int,
        endpoint: str = "",
    ) -> APIResponse:
        """
        删除资源
        
        Args:
            resource_id: 资源ID
            endpoint: 端点路径
        
        Returns:
            API响应
        """
        full_endpoint = self._build_endpoint(endpoint, str(resource_id))
        return await self.client.delete(full_endpoint)
    
    async def _action(
        self,
        resource_id: int,
        action: str,
        data: Optional[Dict[str, Any]] = None,
        method: str = "POST",
    ) -> APIResponse:
        """
        执行资源操作
        
        Args:
            resource_id: 资源ID
            action: 操作名称
            data: 操作数据
            method: HTTP方法
        
        Returns:
            API响应
        """
        full_endpoint = self._build_endpoint(str(resource_id), action)
        
        if method.upper() == "GET":
            return await self.client.get(full_endpoint, params=data)
        elif method.upper() == "POST":
            return await self.client.post(full_endpoint, json_data=data)
        elif method.upper() == "PUT":
            return await self.client.put(full_endpoint, json_data=data)
        elif method.upper() == "DELETE":
            return await self.client.delete(full_endpoint, params=data)
        else:
            return await self.client.request(method, full_endpoint, json_data=data)


class CRUDService(BaseService):
    """支持完整CRUD操作的服务基类"""
    
    async def list(
        self,
        params: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """列出资源"""
        return await self._list(params=params, pagination=pagination)
    
    async def get(self, resource_id: int) -> APIResponse:
        """获取资源"""
        return await self._get(resource_id)
    
    async def create(self, data: Dict[str, Any]) -> APIResponse:
        """创建资源"""
        return await self._create(data)
    
    async def update(self, resource_id: int, data: Dict[str, Any]) -> APIResponse:
        """更新资源"""
        return await self._update(resource_id, data)
    
    async def delete(self, resource_id: int) -> APIResponse:
        """删除资源"""
        return await self._delete(resource_id)


class SearchableService(CRUDService):
    """支持搜索的服务基类"""
    
    async def search(
        self,
        search_params: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        搜索资源
        
        Args:
            search_params: 搜索参数
            pagination: 分页参数
        
        Returns:
            API响应
        """
        params = {}
        if search_params:
            for key, value in search_params.items():
                if not key.startswith("search["):
                    params[f"search[{key}]"] = value
                else:
                    params[key] = value
        
        return await self._list(params=params, pagination=pagination)


class VersionedService(SearchableService):
    """支持版本控制的服务基类"""
    
    _versions_endpoint: str = ""
    
    async def get_versions(
        self,
        resource_id: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取版本历史
        
        Args:
            resource_id: 资源ID（可选，为None时获取所有版本）
            params: 查询参数
            pagination: 分页参数
        
        Returns:
            API响应
        """
        endpoint = self._versions_endpoint or f"{self._endpoint_prefix}_versions"
        query_params = params or {}
        
        if resource_id:
            # 获取特定资源的版本
            parent_key = self._endpoint_prefix.rstrip('s') + "_id"
            query_params[f"search[{parent_key}]"] = resource_id
        
        return await self.client.get(
            endpoint,
            params=self._apply_pagination(query_params, pagination)
        )
    
    async def revert(
        self,
        resource_id: int,
        version_id: Optional[int] = None,
    ) -> APIResponse:
        """
        恢复到指定版本
        
        Args:
            resource_id: 资源ID
            version_id: 版本ID（可选）
        
        Returns:
            API响应
        """
        data = {}
        if version_id:
            data["version_id"] = version_id
        
        return await self._action(resource_id, "revert", data, method="PUT")