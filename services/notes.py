"""
Danbooru API Plugin - Notes 服务
注释相关的所有API操作
"""

from typing import Optional, Dict, Any, List

from .base import VersionedService
from core.models import (
    PaginationParams,
    APIResponse,
    Note,
)
from events.event_types import NoteEvent, NoteEvents


class NotesService(VersionedService):
    """注释服务 - 处理所有注释相关的API操作"""
    
    _endpoint_prefix = "notes"
    _versions_endpoint = "note_versions"
    
    # ==================== 基础CRUD操作 ====================
    
    async def list(
        self,
        post_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        creator_name: Optional[str] = None,
        body_matches: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取注释列表
        
        Args:
            post_id: 帖子ID
            creator_id: 创建者ID
            creator_name: 创建者名称
            body_matches: 内容匹配
            is_active: 是否激活
            page: 页码
            limit: 每页数量
            **kwargs: 其他搜索参数
        
        Returns:
            注释列表响应
        """
        params = {}
        
        if post_id:
            params["search[post_id]"] = post_id
        if creator_id:
            params["search[creator_id]"] = creator_id
        if creator_name:
            params["search[creator_name]"] = creator_name
        if body_matches:
            params["search[body_matches]"] = body_matches
        if is_active is not None:
            params["search[is_active]"] = str(is_active).lower()
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        response = await self._list(params=params, pagination=pagination)
        
        if response.success:
            await self._emit_event(NoteEvent(
                event_type=NoteEvents.SEARCHED,
                post_id=post_id,
            ))
        
        return response
    
    async def get(self, note_id: int) -> APIResponse:
        """
        获取单个注释
        
        Args:
            note_id: 注释ID
        
        Returns:
            注释详情响应
        """
        response = await self._get(note_id)
        
        if response.success:
            await self._emit_event(NoteEvent(
                event_type=NoteEvents.FETCHED,
                note_id=note_id,
                note_data=response.data,
            ))
        
        return response
    
    async def create(
        self,
        post_id: int,
        x: int,
        y: int,
        width: int,
        height: int,
        body: str,
    ) -> APIResponse:
        """
        创建注释
        
        Args:
            post_id: 帖子ID
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            body: 注释内容
        
        Returns:
            创建响应
        """
        data = {
            "note": {
                "post_id": post_id,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "body": body,
            }
        }
        
        response = await self._create(data)
        
        if response.success:
            await self._emit_event(NoteEvent(
                event_type=NoteEvents.CREATED,
                post_id=post_id,
                note_data=response.data,
            ))
        
        return response
    
    async def update(
        self,
        note_id: int,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        body: Optional[str] = None,
    ) -> APIResponse:
        """
        更新注释
        
        Args:
            note_id: 注释ID
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            body: 注释内容
        
        Returns:
            更新响应
        """
        data = {"note": {}}
        
        if x is not None:
            data["note"]["x"] = x
        if y is not None:
            data["note"]["y"] = y
        if width is not None:
            data["note"]["width"] = width
        if height is not None:
            data["note"]["height"] = height
        if body is not None:
            data["note"]["body"] = body
        
        response = await self._update(note_id, data)
        
        if response.success:
            await self._emit_event(NoteEvent(
                event_type=NoteEvents.UPDATED,
                note_id=note_id,
                note_data=response.data,
            ))
        
        return response
    
    async def delete(self, note_id: int) -> APIResponse:
        """
        删除注释
        
        Args:
            note_id: 注释ID
        
        Returns:
            删除响应
        """
        response = await self._delete(note_id)
        
        if response.success:
            await self._emit_event(NoteEvent(
                event_type=NoteEvents.DELETED,
                note_id=note_id,
            ))
        
        return response
    
    # ==================== 版本控制 ====================
    
    async def revert(self, note_id: int, version_id: int) -> APIResponse:
        """
        恢复到指定版本
        
        Args:
            note_id: 注释ID
            version_id: 版本ID
        
        Returns:
            恢复响应
        """
        data = {"version_id": version_id}
        response = await self.client.put(f"notes/{note_id}/revert", json_data=data)
        
        if response.success:
            await self._emit_event(NoteEvent(
                event_type=NoteEvents.REVERTED,
                note_id=note_id,
            ))
        
        return response
    
    async def get_versions(
        self,
        note_id: Optional[int] = None,
        post_id: Optional[int] = None,
        updater_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取注释版本历史
        
        Args:
            note_id: 注释ID
            post_id: 帖子ID
            updater_id: 更新者ID
            pagination: 分页参数
        
        Returns:
            版本列表响应
        """
        params = {}
        
        if note_id:
            params["search[note_id]"] = note_id
        if post_id:
            params["search[post_id]"] = post_id
        if updater_id:
            params["search[updater_id]"] = updater_id
        
        return await self.client.get(
            "note_versions",
            params=self._apply_pagination(params, pagination)
        )

    async def get_version(self, version_id: int) -> APIResponse:
        """获取单个注释版本"""
        return await self.client.get(f"note_versions/{version_id}")

    async def get_preview(self, note_id: int) -> APIResponse:
        """获取注释预览"""
        return await self.client.get(f"note_previews/{note_id}")
    
    async def get_version(self, version_id: int) -> APIResponse:
        """
        获取单个版本详情
        
        Args:
            version_id: 版本ID
        
        Returns:
            版本详情响应
        """
        return await self.client.get(f"note_versions/{version_id}")
    
    # ==================== 预览 ====================
    
    async def preview(self, body: str) -> APIResponse:
        """
        预览注释内容
        
        Args:
            body: 注释内容
        
        Returns:
            预览响应（HTML格式）
        """
        return await self.client.get("note_previews", params={"body": body})
    
    # ==================== 工具方法 ====================
    
    def parse_note(self, data: Dict[str, Any]) -> Note:
        """解析注释数据"""
        return Note.from_dict(data)
    
    def parse_notes(self, data: List[Dict[str, Any]]) -> List[Note]:
        """解析注释列表"""
        return [Note.from_dict(item) for item in data]
    
    async def get_parsed(self, note_id: int) -> Optional[Note]:
        """获取并解析注释"""
        response = await self.get(note_id)
        if response.success and response.data:
            return self.parse_note(response.data)
        return None
    
    async def get_by_post(
        self,
        post_id: int,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Note]:
        """
        获取帖子的所有注释
        
        Args:
            post_id: 帖子ID
            page: 页码
            limit: 每页数量
        
        Returns:
            Note对象列表
        """
        response = await self.list(post_id=post_id, page=page, limit=limit)
        if response.success and isinstance(response.data, list):
            return self.parse_notes(response.data)
        return []
