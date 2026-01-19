"""
Danbooru API Plugin - Forum 服务
论坛相关的所有API操作
"""

from typing import Optional

from .base import CRUDService
from ..core.models import (
    PaginationParams,
    APIResponse,
)


class ForumService(CRUDService):
    """论坛服务 - 处理所有论坛相关的API操作"""
    
    _endpoint_prefix = "forum_topics"
    
    # ==================== 话题操作 ====================
    
    async def list_topics(
        self,
        title_matches: Optional[str] = None,
        category_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        is_sticky: Optional[bool] = None,
        is_locked: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取论坛话题列表
        
        Args:
            title_matches: 标题匹配
            category_id: 分类ID
            creator_id: 创建者ID
            is_sticky: 是否置顶
            is_locked: 是否锁定
            is_deleted: 是否已删除
            page: 页码
            limit: 每页数量
            order: 排序方式
            **kwargs: 其他搜索参数
        
        Returns:
            话题列表响应
        """
        params = {}
        
        if title_matches:
            params["search[title_matches]"] = title_matches
        if category_id:
            params["search[category_id]"] = category_id
        if creator_id:
            params["search[creator_id]"] = creator_id
        if is_sticky is not None:
            params["search[is_sticky]"] = str(is_sticky).lower()
        if is_locked is not None:
            params["search[is_locked]"] = str(is_locked).lower()
        if is_deleted is not None:
            params["search[is_deleted]"] = str(is_deleted).lower()
        if order:
            params["search[order]"] = order
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        return await self._list(params=params, pagination=pagination)
    
    async def get_topic(self, topic_id: int) -> APIResponse:
        """
        获取单个话题
        
        Args:
            topic_id: 话题ID
        
        Returns:
            话题详情响应
        """
        return await self._get(topic_id)
    
    async def create_topic(
        self,
        title: str,
        category_id: int,
        original_post_body: str,
        is_sticky: bool = False,
        is_locked: bool = False,
    ) -> APIResponse:
        """
        创建话题
        
        Args:
            title: 标题
            category_id: 分类ID
            original_post_body: 首帖内容
            is_sticky: 是否置顶
            is_locked: 是否锁定
        
        Returns:
            创建响应
        """
        data = {
            "forum_topic": {
                "title": title,
                "category_id": category_id,
                "original_post_attributes": {
                    "body": original_post_body
                },
                "is_sticky": is_sticky,
                "is_locked": is_locked,
            }
        }
        
        return await self._create(data)
    
    async def update_topic(
        self,
        topic_id: int,
        title: Optional[str] = None,
        category_id: Optional[int] = None,
        is_sticky: Optional[bool] = None,
        is_locked: Optional[bool] = None,
    ) -> APIResponse:
        """
        更新话题
        
        Args:
            topic_id: 话题ID
            title: 新标题
            category_id: 新分类ID
            is_sticky: 是否置顶
            is_locked: 是否锁定
        
        Returns:
            更新响应
        """
        data = {"forum_topic": {}}
        
        if title:
            data["forum_topic"]["title"] = title
        if category_id:
            data["forum_topic"]["category_id"] = category_id
        if is_sticky is not None:
            data["forum_topic"]["is_sticky"] = is_sticky
        if is_locked is not None:
            data["forum_topic"]["is_locked"] = is_locked
        
        return await self._update(topic_id, data)
    
    async def delete_topic(self, topic_id: int) -> APIResponse:
        """
        删除话题
        
        Args:
            topic_id: 话题ID
        
        Returns:
            删除响应
        """
        return await self._delete(topic_id)
    
    async def undelete_topic(self, topic_id: int) -> APIResponse:
        """
        恢复已删除的话题
        
        Args:
            topic_id: 话题ID
        
        Returns:
            恢复响应
        """
        return await self.client.post(f"forum_topics/{topic_id}/undelete")
    
    async def mark_all_as_read(self) -> APIResponse:
        """
        标记所有话题为已读
        
        Returns:
            操作响应
        """
        return await self.client.post("forum_topics/mark_all_as_read")
    
    # ==================== 帖子操作 ====================
    
    async def list_posts(
        self,
        topic_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        body_matches: Optional[str] = None,
        is_deleted: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取论坛帖子列表
        
        Args:
            topic_id: 话题ID
            creator_id: 创建者ID
            body_matches: 内容匹配
            is_deleted: 是否已删除
            page: 页码
            limit: 每页数量
            **kwargs: 其他搜索参数
        
        Returns:
            帖子列表响应
        """
        params = {}
        
        if topic_id:
            params["search[topic_id]"] = topic_id
        if creator_id:
            params["search[creator_id]"] = creator_id
        if body_matches:
            params["search[body_matches]"] = body_matches
        if is_deleted is not None:
            params["search[is_deleted]"] = str(is_deleted).lower()
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        return await self.client.get(
            "forum_posts",
            params=self._apply_pagination(params, pagination)
        )
    
    async def get_post(self, post_id: int) -> APIResponse:
        """
        获取单个帖子
        
        Args:
            post_id: 帖子ID
        
        Returns:
            帖子详情响应
        """
        return await self.client.get(f"forum_posts/{post_id}")
    
    async def create_post(
        self,
        topic_id: int,
        body: str,
    ) -> APIResponse:
        """
        创建帖子
        
        Args:
            topic_id: 话题ID
            body: 帖子内容
        
        Returns:
            创建响应
        """
        data = {
            "forum_post": {
                "topic_id": topic_id,
                "body": body,
            }
        }
        
        return await self.client.post("forum_posts", json_data=data)
    
    async def update_post(
        self,
        post_id: int,
        body: str,
    ) -> APIResponse:
        """
        更新帖子
        
        Args:
            post_id: 帖子ID
            body: 新内容
        
        Returns:
            更新响应
        """
        data = {
            "forum_post": {
                "body": body,
            }
        }
        
        return await self.client.put(f"forum_posts/{post_id}", json_data=data)
    
    async def delete_post(self, post_id: int) -> APIResponse:
        """
        删除帖子
        
        Args:
            post_id: 帖子ID
        
        Returns:
            删除响应
        """
        return await self.client.delete(f"forum_posts/{post_id}")
    
    async def undelete_post(self, post_id: int) -> APIResponse:
        """
        恢复已删除的帖子
        
        Args:
            post_id: 帖子ID
        
        Returns:
            恢复响应
        """
        return await self.client.post(f"forum_posts/{post_id}/undelete")
    
    async def search_posts(
        self,
        body_matches: Optional[str] = None,
        topic_title_matches: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
        **kwargs
    ) -> APIResponse:
        """
        搜索论坛帖子
        
        Args:
            body_matches: 内容匹配
            topic_title_matches: 话题标题匹配
            pagination: 分页参数
            **kwargs: 其他搜索参数
        
        Returns:
            搜索结果
        """
        params = {}
        
        if body_matches:
            params["search[body_matches]"] = body_matches
        if topic_title_matches:
            params["search[topic_title_matches]"] = topic_title_matches
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        return await self.client.get(
            "forum_posts/search",
            params=self._apply_pagination(params, pagination)
        )
    
    # ==================== 投票操作 ====================
    
    async def list_post_votes(
        self,
        forum_post_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取帖子投票列表
        
        Args:
            forum_post_id: 帖子ID
            creator_id: 投票者ID
            pagination: 分页参数
        
        Returns:
            投票列表响应
        """
        params = {}
        
        if forum_post_id:
            params["search[forum_post_id]"] = forum_post_id
        if creator_id:
            params["search[creator_id]"] = creator_id
        
        return await self.client.get(
            "forum_post_votes",
            params=self._apply_pagination(params, pagination)
        )
    
    async def vote_post(self, forum_post_id: int, score: int = 1) -> APIResponse:
        """
        为帖子投票
        
        Args:
            forum_post_id: 帖子ID
            score: 分数（1或-1）
        
        Returns:
            投票响应
        """
        data = {
            "forum_post_vote": {
                "forum_post_id": forum_post_id,
                "score": score,
            }
        }
        
        return await self.client.post("forum_post_votes", json_data=data)
    
    async def unvote_post(self, vote_id: int) -> APIResponse:
        """
        取消帖子投票
        
        Args:
            vote_id: 投票ID
        
        Returns:
            取消投票响应
        """
        return await self.client.delete(f"forum_post_votes/{vote_id}")
    
    # ==================== 话题访问记录 ====================
    
    async def list_topic_visits(
        self,
        user_id: Optional[int] = None,
        forum_topic_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取话题访问记录
        
        Args:
            user_id: 用户ID
            forum_topic_id: 话题ID
            pagination: 分页参数
        
        Returns:
            访问记录列表响应
        """
        params = {}
        
        if user_id:
            params["search[user_id]"] = user_id
        if forum_topic_id:
            params["search[forum_topic_id]"] = forum_topic_id
        
        return await self.client.get(
            "forum_topic_visits",
            params=self._apply_pagination(params, pagination)
        )