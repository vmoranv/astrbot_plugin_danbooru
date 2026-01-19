"""
Danbooru API Plugin - Favorites 服务
收藏相关的所有API操作
"""

from typing import Optional, Dict, Any, List

from .base import BaseService
from core.models import (
    PaginationParams,
    APIResponse,
    Favorite,
    FavoriteGroup,
)
from events.event_types import FavoriteEvent, FavoriteEvents


class FavoritesService(BaseService):
    """收藏服务 - 处理所有收藏相关的API操作"""
    
    _endpoint_prefix = "favorites"
    
    # ==================== 收藏操作 ====================
    
    async def list(
        self,
        user_id: Optional[int] = None,
        post_id: Optional[int] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取收藏列表
        
        Args:
            user_id: 用户ID
            post_id: 帖子ID
            page: 页码
            limit: 每页数量
            **kwargs: 其他搜索参数
        
        Returns:
            收藏列表响应
        """
        params = {}
        
        if user_id:
            params["search[user_id]"] = user_id
        if post_id:
            params["search[post_id]"] = post_id
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        response = await self._list(params=params, pagination=pagination)
        
        if response.success:
            await self._emit_event(FavoriteEvent(
                event_type=FavoriteEvents.LISTED,
                user_id=user_id,
                post_id=post_id,
            ))
        
        return response
    
    async def create(self, post_id: int) -> APIResponse:
        """
        添加收藏
        
        Args:
            post_id: 帖子ID
        
        Returns:
            创建响应
        """
        data = {"post_id": post_id}
        response = await self._create(data)
        
        if response.success:
            await self._emit_event(FavoriteEvent(
                event_type=FavoriteEvents.ADDED,
                post_id=post_id,
            ))
        
        return response
    
    async def delete(self, post_id: int) -> APIResponse:
        """
        取消收藏
        
        Args:
            post_id: 帖子ID
        
        Returns:
            删除响应
        """
        response = await self._delete(post_id)
        
        if response.success:
            await self._emit_event(FavoriteEvent(
                event_type=FavoriteEvents.REMOVED,
                post_id=post_id,
            ))
        
        return response
    
    # ==================== 收藏组操作 ====================
    
    async def list_groups(
        self,
        creator_id: Optional[int] = None,
        creator_name: Optional[str] = None,
        name_matches: Optional[str] = None,
        is_public: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取收藏组列表
        
        Args:
            creator_id: 创建者ID
            creator_name: 创建者名称
            name_matches: 名称匹配
            is_public: 是否公开
            page: 页码
            limit: 每页数量
            **kwargs: 其他搜索参数
        
        Returns:
            收藏组列表响应
        """
        params = {}
        
        if creator_id:
            params["search[creator_id]"] = creator_id
        if creator_name:
            params["search[creator_name]"] = creator_name
        if name_matches:
            params["search[name_matches]"] = name_matches
        if is_public is not None:
            params["search[is_public]"] = str(is_public).lower()
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        return await self.client.get(
            "favorite_groups",
            params=self._apply_pagination(params, pagination)
        )
    
    async def get_group(self, group_id: int) -> APIResponse:
        """
        获取单个收藏组
        
        Args:
            group_id: 收藏组ID
        
        Returns:
            收藏组详情响应
        """
        return await self.client.get(f"favorite_groups/{group_id}")
    
    async def create_group(
        self,
        name: str,
        is_public: bool = True,
        post_ids: Optional[List[int]] = None,
    ) -> APIResponse:
        """
        创建收藏组
        
        Args:
            name: 收藏组名称
            is_public: 是否公开
            post_ids: 初始帖子ID列表
        
        Returns:
            创建响应
        """
        data = {
            "favorite_group": {
                "name": name,
                "is_public": is_public,
            }
        }
        
        if post_ids:
            data["favorite_group"]["post_ids_string"] = " ".join(map(str, post_ids))
        
        return await self.client.post("favorite_groups", json_data=data)
    
    async def update_group(
        self,
        group_id: int,
        name: Optional[str] = None,
        is_public: Optional[bool] = None,
        post_ids: Optional[List[int]] = None,
    ) -> APIResponse:
        """
        更新收藏组
        
        Args:
            group_id: 收藏组ID
            name: 新名称
            is_public: 是否公开
            post_ids: 帖子ID列表
        
        Returns:
            更新响应
        """
        data = {"favorite_group": {}}
        
        if name is not None:
            data["favorite_group"]["name"] = name
        if is_public is not None:
            data["favorite_group"]["is_public"] = is_public
        if post_ids is not None:
            data["favorite_group"]["post_ids_string"] = " ".join(map(str, post_ids))
        
        return await self.client.put(f"favorite_groups/{group_id}", json_data=data)
    
    async def delete_group(self, group_id: int) -> APIResponse:
        """
        删除收藏组
        
        Args:
            group_id: 收藏组ID
        
        Returns:
            删除响应
        """
        return await self.client.delete(f"favorite_groups/{group_id}")
    
    async def add_post_to_group(self, group_id: int, post_id: int) -> APIResponse:
        """
        添加帖子到收藏组
        
        Args:
            group_id: 收藏组ID
            post_id: 帖子ID
        
        Returns:
            添加响应
        """
        data = {"post_id": post_id}
        return await self.client.put(f"favorite_groups/{group_id}/add_post", json_data=data)
    
    async def remove_post_from_group(self, group_id: int, post_id: int) -> APIResponse:
        """
        从收藏组移除帖子
        
        Args:
            group_id: 收藏组ID
            post_id: 帖子ID
        
        Returns:
            移除响应
        """
        # 获取当前帖子列表并移除指定帖子
        group_response = await self.get_group(group_id)
        if not group_response.success:
            return group_response
        
        current_post_ids = group_response.data.get("post_ids", [])
        if post_id in current_post_ids:
            current_post_ids.remove(post_id)
        
        return await self.update_group(group_id, post_ids=current_post_ids)
    
    async def get_group_order(self, group_id: int) -> APIResponse:
        """
        获取收藏组排序信息
        
        Args:
            group_id: 收藏组ID
        
        Returns:
            排序信息响应
        """
        return await self.client.get(f"favorite_groups/{group_id}/order/edit")
    
    async def get_user_groups(
        self,
        user_id: int,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> APIResponse:
        """
        获取用户的收藏组
        
        Args:
            user_id: 用户ID
            page: 页码
            limit: 每页数量
        
        Returns:
            收藏组列表响应
        """
        return await self.list_groups(creator_id=user_id, page=page, limit=limit)
    
    # ==================== 工具方法 ====================
    
    def parse_favorite(self, data: Dict[str, Any]) -> Favorite:
        """解析收藏数据"""
        return Favorite.from_dict(data)
    
    def parse_favorites(self, data: List[Dict[str, Any]]) -> List[Favorite]:
        """解析收藏列表"""
        return [Favorite.from_dict(item) for item in data]
    
    def parse_group(self, data: Dict[str, Any]) -> FavoriteGroup:
        """解析收藏组数据"""
        return FavoriteGroup.from_dict(data)
    
    def parse_groups(self, data: List[Dict[str, Any]]) -> List[FavoriteGroup]:
        """解析收藏组列表"""
        return [FavoriteGroup.from_dict(item) for item in data]
    
    async def is_favorited(self, post_id: int, user_id: int) -> bool:
        """
        检查帖子是否已被收藏
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
        
        Returns:
            是否已收藏
        """
        response = await self.list(post_id=post_id, user_id=user_id, limit=1)
        if response.success and isinstance(response.data, list):
            return len(response.data) > 0
        return False