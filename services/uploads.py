"""
Danbooru API Plugin - Uploads 服务
上传相关的所有API操作
"""

from typing import Optional

from .base import BaseService
from core.models import (
    PaginationParams,
    APIResponse,
)


class UploadsService(BaseService):
    """上传服务 - 处理所有上传相关的API操作"""
    
    _endpoint_prefix = "uploads"
    
    # ==================== 基础CRUD操作 ====================
    
    async def list(
        self,
        uploader_id: Optional[int] = None,
        uploader_name: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        has_post: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取上传列表
        
        Args:
            uploader_id: 上传者ID
            uploader_name: 上传者名称
            source: 来源URL
            status: 状态（pending, completed, error）
            has_post: 是否已有帖子
            page: 页码
            limit: 每页数量
            **kwargs: 其他搜索参数
        
        Returns:
            上传列表响应
        """
        params = {}
        
        if uploader_id:
            params["search[uploader_id]"] = uploader_id
        if uploader_name:
            params["search[uploader_name]"] = uploader_name
        if source:
            params["search[source]"] = source
        if status:
            params["search[status]"] = status
        if has_post is not None:
            params["search[has_post]"] = str(has_post).lower()
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        return await self._list(params=params, pagination=pagination)
    
    async def get(self, upload_id: int) -> APIResponse:
        """
        获取单个上传信息
        
        Args:
            upload_id: 上传ID
        
        Returns:
            上传详情响应
        """
        return await self._get(upload_id)
    
    async def create(
        self,
        source: Optional[str] = None,
        file: Optional[str] = None,
        tag_string: Optional[str] = None,
        rating: Optional[str] = None,
        parent_id: Optional[int] = None,
        **kwargs
    ) -> APIResponse:
        """
        创建上传
        
        Args:
            source: 来源URL
            file: 文件（base64或路径）
            tag_string: 标签字符串
            rating: 分级
            parent_id: 父帖子ID
            **kwargs: 其他参数
        
        Returns:
            创建响应
        """
        data = {"upload": {}}
        
        if source:
            data["upload"]["source"] = source
        if file:
            data["upload"]["file"] = file
        if tag_string:
            data["upload"]["tag_string"] = tag_string
        if rating:
            data["upload"]["rating"] = rating
        if parent_id:
            data["upload"]["parent_id"] = parent_id
        
        for key, value in kwargs.items():
            if value is not None:
                data["upload"][key] = value
        
        return await self._create(data)
    
    async def update(
        self,
        upload_id: int,
        tag_string: Optional[str] = None,
        rating: Optional[str] = None,
        parent_id: Optional[int] = None,
        **kwargs
    ) -> APIResponse:
        """
        更新上传
        
        Args:
            upload_id: 上传ID
            tag_string: 标签字符串
            rating: 分级
            parent_id: 父帖子ID
            **kwargs: 其他参数
        
        Returns:
            更新响应
        """
        data = {"upload": {}}
        
        if tag_string:
            data["upload"]["tag_string"] = tag_string
        if rating:
            data["upload"]["rating"] = rating
        if parent_id:
            data["upload"]["parent_id"] = parent_id
        
        for key, value in kwargs.items():
            if value is not None:
                data["upload"][key] = value
        
        return await self._update(upload_id, data)
    
    async def delete(self, upload_id: int) -> APIResponse:
        """
        删除上传
        
        Args:
            upload_id: 上传ID
        
        Returns:
            删除响应
        """
        return await self._delete(upload_id)
    
    # ==================== 预处理操作 ====================
    
    async def preprocess(
        self,
        source: Optional[str] = None,
        file: Optional[str] = None,
    ) -> APIResponse:
        """
        预处理上传（获取源信息）
        
        Args:
            source: 来源URL
            file: 文件
        
        Returns:
            预处理响应
        """
        data = {}
        if source:
            data["source"] = source
        if file:
            data["file"] = file
        
        return await self.client.post("uploads/preprocess", json_data=data)
    
    # ==================== 批量操作 ====================
    
    async def batch(self) -> APIResponse:
        """
        获取批量上传页面
        
        Returns:
            批量上传响应
        """
        return await self.client.get("uploads/batch")
    
    # ==================== 代理操作 ====================
    
    async def image_proxy(self, url: str) -> APIResponse:
        """
        通过代理获取图片
        
        Args:
            url: 图片URL
        
        Returns:
            代理响应
        """
        return await self.client.get("uploads/image_proxy", params={"url": url})