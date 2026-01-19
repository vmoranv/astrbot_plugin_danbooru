"""
Danbooru API Plugin - Pools 服务
图池相关的所有API操作
"""

from typing import Optional, Dict, Any, List

from .base import VersionedService
from core.models import (
    PaginationParams,
    APIResponse,
    Pool,
)
from events.event_types import PoolEvent, PoolEvents


class PoolsService(VersionedService):
    """图池服务 - 处理所有图池相关的API操作"""
    
    _endpoint_prefix = "pools"
    _versions_endpoint = "pool_versions"
    
    # ==================== 基础CRUD操作 ====================
    
    async def list(
        self,
        name_matches: Optional[str] = None,
        description_matches: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取图池列表
        
        Args:
            name_matches: 名称匹配（支持通配符*）
            description_matches: 描述匹配
            category: 类别 (series, collection)
            is_active: 是否活跃
            is_deleted: 是否已删除
            page: 页码
            limit: 每页数量
            order: 排序方式
            **kwargs: 其他搜索参数
        
        Returns:
            图池列表响应
        """
        params = {}
        
        if name_matches:
            params["search[name_matches]"] = name_matches
        if description_matches:
            params["search[description_matches]"] = description_matches
        if category:
            params["search[category]"] = category
        if is_active is not None:
            params["search[is_active]"] = str(is_active).lower()
        if is_deleted is not None:
            params["search[is_deleted]"] = str(is_deleted).lower()
        if order:
            params["search[order]"] = order
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        response = await self._list(params=params, pagination=pagination)
        
        if response.success:
            await self._emit_event(PoolEvent(
                event_type=PoolEvents.SEARCHED,
                pool_name=name_matches,
            ))
        
        return response
    
    async def get(self, pool_id: int) -> APIResponse:
        """
        获取单个图池
        
        Args:
            pool_id: 图池ID
        
        Returns:
            图池详情响应
        """
        response = await self._get(pool_id)
        
        if response.success:
            await self._emit_event(PoolEvent(
                event_type=PoolEvents.FETCHED,
                pool_id=pool_id,
                pool_data=response.data,
            ))
        
        return response
    
    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        category: str = "series",
        is_active: bool = True,
        post_ids: Optional[List[int]] = None,
    ) -> APIResponse:
        """
        创建图池
        
        Args:
            name: 图池名称
            description: 描述
            category: 类别 (series, collection)
            is_active: 是否活跃
            post_ids: 初始帖子ID列表
        
        Returns:
            创建响应
        """
        data = {
            "pool": {
                "name": name,
                "category": category,
                "is_active": is_active,
            }
        }
        
        if description:
            data["pool"]["description"] = description
        if post_ids:
            data["pool"]["post_ids_string"] = " ".join(map(str, post_ids))
        
        response = await self._create(data)
        
        if response.success:
            await self._emit_event(PoolEvent(
                event_type=PoolEvents.CREATED,
                pool_name=name,
                pool_data=response.data,
            ))
        
        return response
    
    async def update(
        self,
        pool_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        post_ids: Optional[List[int]] = None,
    ) -> APIResponse:
        """
        更新图池
        
        Args:
            pool_id: 图池ID
            name: 新名称
            description: 新描述
            category: 新类别
            is_active: 是否活跃
            post_ids: 帖子ID列表
        
        Returns:
            更新响应
        """
        data = {"pool": {}}
        
        if name is not None:
            data["pool"]["name"] = name
        if description is not None:
            data["pool"]["description"] = description
        if category is not None:
            data["pool"]["category"] = category
        if is_active is not None:
            data["pool"]["is_active"] = is_active
        if post_ids is not None:
            data["pool"]["post_ids_string"] = " ".join(map(str, post_ids))
        
        response = await self._update(pool_id, data)
        
        if response.success:
            await self._emit_event(PoolEvent(
                event_type=PoolEvents.UPDATED,
                pool_id=pool_id,
                pool_data=response.data,
            ))
        
        return response
    
    async def delete(self, pool_id: int) -> APIResponse:
        """
        删除图池
        
        Args:
            pool_id: 图池ID
        
        Returns:
            删除响应
        """
        response = await self._delete(pool_id)
        
        if response.success:
            await self._emit_event(PoolEvent(
                event_type=PoolEvents.DELETED,
                pool_id=pool_id,
            ))
        
        return response


    async def create_pool_element(self, pool_id: int, post_id: int) -> APIResponse:
        """创建图池元素"""
        data = {"pool_element": {"pool_id": pool_id, "post_id": post_id}}
        return await self.client.post("pool_element", json_data=data)
    
    # ==================== 帖子管理 ====================
    
    async def add_post(self, pool_id: int, post_id: int) -> APIResponse:
        """
        添加帖子到图池
        
        Args:
            pool_id: 图池ID
            post_id: 帖子ID
        
        Returns:
            添加响应
        """
        data = {"post_id": post_id}
        response = await self.client.put(f"pools/{pool_id}/add_post", json_data=data)
        
        if response.success:
            await self._emit_event(PoolEvent(
                event_type=PoolEvents.POST_ADDED,
                pool_id=pool_id,
                pool_data={"post_id": post_id},
            ))
        
        return response
    
    async def remove_post(self, pool_id: int, post_id: int) -> APIResponse:
        """
        从图池移除帖子
        
        Args:
            pool_id: 图池ID
            post_id: 帖子ID
        
        Returns:
            移除响应
        """
        # 获取当前帖子列表并移除指定帖子
        pool_response = await self.get(pool_id)
        if not pool_response.success:
            return pool_response
        
        current_post_ids = pool_response.data.get("post_ids", [])
        if post_id in current_post_ids:
            current_post_ids.remove(post_id)
        
        response = await self.update(pool_id, post_ids=current_post_ids)
        
        if response.success:
            await self._emit_event(PoolEvent(
                event_type=PoolEvents.POST_REMOVED,
                pool_id=pool_id,
                pool_data={"post_id": post_id},
            ))
        
        return response
    
    async def reorder_posts(
        self,
        pool_id: int,
        post_ids: List[int],
    ) -> APIResponse:
        """
        重新排序图池中的帖子
        
        Args:
            pool_id: 图池ID
            post_ids: 新的帖子ID顺序
        
        Returns:
            更新响应
        """
        return await self.update(pool_id, post_ids=post_ids)
    
    # ==================== 版本控制 ====================
    
    async def revert(self, pool_id: int, version_id: int) -> APIResponse:
        """
        恢复到指定版本
        
        Args:
            pool_id: 图池ID
            version_id: 版本ID
        
        Returns:
            恢复响应
        """
        data = {"version_id": version_id}
        return await self.client.put(f"pools/{pool_id}/revert", json_data=data)
    
    async def undelete(self, pool_id: int) -> APIResponse:
        """
        恢复已删除的图池
        
        Args:
            pool_id: 图池ID
        
        Returns:
            恢复响应
        """
        return await self.client.post(f"pools/{pool_id}/undelete")
    
    async def get_versions(
        self,
        pool_id: Optional[int] = None,
        updater_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取图池版本历史
        
        Args:
            pool_id: 图池ID
            updater_id: 更新者ID
            pagination: 分页参数
        
        Returns:
            版本列表响应
        """
        params = {}
        
        if pool_id:
            params["search[pool_id]"] = pool_id
        if updater_id:
            params["search[updater_id]"] = updater_id
        
        return await self.client.get(
            "pool_versions",
            params=self._apply_pagination(params, pagination)
        )
    
    async def get_version_diff(
        self,
        version_id: int,
    ) -> APIResponse:
        """
        获取版本差异
        
        Args:
            version_id: 版本ID
        
        Returns:
            版本差异响应
        """
        return await self.client.get(f"pool_versions/{version_id}/diff")
    
    async def search_versions(self, **kwargs) -> APIResponse:
        """
        搜索版本
        
        Args:
            **kwargs: 搜索参数
        
        Returns:
            搜索结果
        """
        params = {}
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        return await self.client.get("pool_versions/search", params=params)
    
    # ==================== 画廊视图 ====================
    
    async def gallery(
        self,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取图池画廊
        
        Args:
            pagination: 分页参数
        
        Returns:
            画廊响应
        """
        params = self._apply_pagination({}, pagination)
        return await self.client.get("pools/gallery", params=params)
    
    # ==================== 排序操作 ====================
    
    async def get_order(self, pool_id: int) -> APIResponse:
        """
        获取图池排序信息
        
        Args:
            pool_id: 图池ID
        
        Returns:
            排序信息响应
        """
        return await self.client.get(f"pools/{pool_id}/order/edit")
    
    # ==================== 工具方法 ====================
    
    def parse_pool(self, data: Dict[str, Any]) -> Pool:
        """解析图池数据"""
        return Pool.from_dict(data)
    
    def parse_pools(self, data: List[Dict[str, Any]]) -> List[Pool]:
        """解析图池列表"""
        return [Pool.from_dict(item) for item in data]
    
    async def get_parsed(self, pool_id: int) -> Optional[Pool]:
        """获取并解析图池"""
        response = await self.get(pool_id)
        if response.success and response.data:
            return self.parse_pool(response.data)
        return None
    
    async def find_by_name(self, name: str) -> Optional[Pool]:
        """
        按名称查找图池
        
        Args:
            name: 图池名称
        
        Returns:
            Pool对象或None
        """
        response = await self.list(name_matches=name, limit=1)
        if response.success and isinstance(response.data, list) and len(response.data) > 0:
            return self.parse_pool(response.data[0])
        return None
