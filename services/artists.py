"""
Danbooru API Plugin - Artists 服务
艺术家相关的所有API操作
"""

from typing import Optional, Dict, Any, List

from .base import VersionedService
from core.models import (
    PaginationParams,
    APIResponse,
    Artist,
)
from events.event_types import ArtistEvent, ArtistEvents


class ArtistsService(VersionedService):
    """艺术家服务 - 处理所有艺术家相关的API操作"""
    
    _endpoint_prefix = "artists"
    _versions_endpoint = "artist_versions"
    
    # ==================== 基础CRUD操作 ====================
    
    async def list(
        self,
        name: Optional[str] = None,
        name_matches: Optional[str] = None,
        url_matches: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_banned: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取艺术家列表
        
        Args:
            name: 精确匹配艺术家名
            name_matches: 艺术家名匹配（支持通配符*）
            url_matches: URL匹配
            is_active: 是否活跃
            is_banned: 是否被封禁
            page: 页码
            limit: 每页数量
            order: 排序方式
            **kwargs: 其他搜索参数
        
        Returns:
            艺术家列表响应
        """
        params = {}
        
        if name:
            params["search[name]"] = name
        if name_matches:
            params["search[name_matches]"] = name_matches
        if url_matches:
            params["search[url_matches]"] = url_matches
        if is_active is not None:
            params["search[is_active]"] = str(is_active).lower()
        if is_banned is not None:
            params["search[is_banned]"] = str(is_banned).lower()
        if order:
            params["search[order]"] = order
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        response = await self._list(params=params, pagination=pagination)
        
        if response.success:
            await self._emit_event(ArtistEvent(
                event_type=ArtistEvents.SEARCHED,
                artist_name=name_matches or name,
            ))
        
        return response
    
    async def get(self, artist_id: int) -> APIResponse:
        """
        获取单个艺术家
        
        Args:
            artist_id: 艺术家ID
        
        Returns:
            艺术家详情响应
        """
        response = await self._get(artist_id)
        
        if response.success:
            await self._emit_event(ArtistEvent(
                event_type=ArtistEvents.FETCHED,
                artist_id=artist_id,
                artist_data=response.data,
            ))
        
        return response
    
    async def create(
        self,
        name: str,
        other_names: Optional[List[str]] = None,
        urls: Optional[List[str]] = None,
        group_name: Optional[str] = None,
        is_banned: bool = False,
    ) -> APIResponse:
        """
        创建艺术家
        
        Args:
            name: 艺术家名
            other_names: 其他名称列表
            urls: URL列表
            group_name: 组名
            is_banned: 是否封禁
        
        Returns:
            创建响应
        """
        data = {
            "artist": {
                "name": name,
                "is_banned": is_banned,
            }
        }
        
        if other_names:
            data["artist"]["other_names_string"] = " ".join(other_names)
        if urls:
            data["artist"]["url_string"] = "\n".join(urls)
        if group_name:
            data["artist"]["group_name"] = group_name
        
        response = await self._create(data)
        
        if response.success:
            await self._emit_event(ArtistEvent(
                event_type=ArtistEvents.CREATED,
                artist_name=name,
                artist_data=response.data,
            ))
        
        return response
    
    async def update(
        self,
        artist_id: int,
        name: Optional[str] = None,
        other_names: Optional[List[str]] = None,
        urls: Optional[List[str]] = None,
        group_name: Optional[str] = None,
        is_banned: Optional[bool] = None,
    ) -> APIResponse:
        """
        更新艺术家
        
        Args:
            artist_id: 艺术家ID
            name: 新名称
            other_names: 其他名称
            urls: URL列表
            group_name: 组名
            is_banned: 是否封禁
        
        Returns:
            更新响应
        """
        data = {"artist": {}}
        
        if name is not None:
            data["artist"]["name"] = name
        if other_names is not None:
            data["artist"]["other_names_string"] = " ".join(other_names)
        if urls is not None:
            data["artist"]["url_string"] = "\n".join(urls)
        if group_name is not None:
            data["artist"]["group_name"] = group_name
        if is_banned is not None:
            data["artist"]["is_banned"] = is_banned
        
        response = await self._update(artist_id, data)
        
        if response.success:
            await self._emit_event(ArtistEvent(
                event_type=ArtistEvents.UPDATED,
                artist_id=artist_id,
                artist_data=response.data,
            ))
        
        return response
    
    async def delete(self, artist_id: int) -> APIResponse:
        """
        删除艺术家
        
        Args:
            artist_id: 艺术家ID
        
        Returns:
            删除响应
        """
        return await self._delete(artist_id)
    
    # ==================== 特殊操作 ====================
    
    async def show_or_new(self, name: str) -> APIResponse:
        """
        显示艺术家或准备创建新艺术家
        
        Args:
            name: 艺术家名
        
        Returns:
            艺术家信息或创建表单数据
        """
        return await self.client.get("artists/show_or_new", params={"name": name})
    
    async def banned(
        self,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取被封禁的艺术家列表
        
        Args:
            pagination: 分页参数
        
        Returns:
            封禁艺术家列表
        """
        params = self._apply_pagination({}, pagination)
        return await self.client.get("artists/banned", params=params)
    
    async def ban(self, artist_id: int) -> APIResponse:
        """
        封禁艺术家
        
        Args:
            artist_id: 艺术家ID
        
        Returns:
            封禁响应
        """
        response = await self.client.put(f"artists/{artist_id}/ban")
        
        if response.success:
            await self._emit_event(ArtistEvent(
                event_type=ArtistEvents.BANNED,
                artist_id=artist_id,
            ))
        
        return response
    
    async def unban(self, artist_id: int) -> APIResponse:
        """
        解封艺术家
        
        Args:
            artist_id: 艺术家ID
        
        Returns:
            解封响应
        """
        response = await self.client.put(f"artists/{artist_id}/unban")
        
        if response.success:
            await self._emit_event(ArtistEvent(
                event_type=ArtistEvents.UNBANNED,
                artist_id=artist_id,
            ))
        
        return response
    
    async def revert(self, artist_id: int, version_id: int) -> APIResponse:
        """
        恢复到指定版本
        
        Args:
            artist_id: 艺术家ID
            version_id: 版本ID
        
        Returns:
            恢复响应
        """
        data = {"version_id": version_id}
        return await self.client.put(f"artists/{artist_id}/revert", json_data=data)
    
    # ==================== 版本历史 ====================
    
    async def get_versions(
        self,
        artist_id: Optional[int] = None,
        name: Optional[str] = None,
        updater_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取艺术家版本历史
        
        Args:
            artist_id: 艺术家ID
            name: 艺术家名
            updater_id: 更新者ID
            pagination: 分页参数
        
        Returns:
            版本列表响应
        """
        params = {}
        
        if artist_id:
            params["search[artist_id]"] = artist_id
        if name:
            params["search[name]"] = name
        if updater_id:
            params["search[updater_id]"] = updater_id
        
        return await self.client.get(
            "artist_versions",
            params=self._apply_pagination(params, pagination)
        )
    
    async def search_versions(self, **kwargs) -> APIResponse:
        """
        搜索艺术家版本
        
        Args:
            **kwargs: 搜索参数
        
        Returns:
            版本搜索结果
        """
        params = {}
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        return await self.client.get("artist_versions/search", params=params)

    async def get_version(self, version_id: int) -> APIResponse:
        """获取单个艺术家版本"""
        return await self.client.get(f"artist_versions/{version_id}")
    
    # ==================== 艺术家URL ====================
    
    async def get_urls(
        self,
        artist_id: Optional[int] = None,
        url_matches: Optional[str] = None,
        is_active: Optional[bool] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取艺术家URL列表
        
        Args:
            artist_id: 艺术家ID
            url_matches: URL匹配
            is_active: 是否活跃
            pagination: 分页参数
        
        Returns:
            URL列表响应
        """
        params = {}
        
        if artist_id:
            params["search[artist_id]"] = artist_id
        if url_matches:
            params["search[url_matches]"] = url_matches
        if is_active is not None:
            params["search[is_active]"] = str(is_active).lower()
        
        return await self.client.get(
            "artist_urls",
            params=self._apply_pagination(params, pagination)
        )
    
    # ==================== 工具方法 ====================
    
    def parse_artist(self, data: Dict[str, Any]) -> Artist:
        """解析艺术家数据"""
        return Artist.from_dict(data)
    
    def parse_artists(self, data: List[Dict[str, Any]]) -> List[Artist]:
        """解析艺术家列表"""
        return [Artist.from_dict(item) for item in data]
    
    async def get_parsed(self, artist_id: int) -> Optional[Artist]:
        """获取并解析艺术家"""
        response = await self.get(artist_id)
        if response.success and response.data:
            return self.parse_artist(response.data)
        return None
    
    async def find_by_name(self, name: str) -> Optional[Artist]:
        """
        按名称查找艺术家
        
        Args:
            name: 艺术家名
        
        Returns:
            Artist对象或None
        """
        response = await self.list(name=name, limit=1)
        if response.success and isinstance(response.data, list) and len(response.data) > 0:
            return self.parse_artist(response.data[0])
        return None
