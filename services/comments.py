"""
Danbooru API Plugin - Comments 服务
评论相关的所有API操作
"""

from typing import Optional, Dict, Any, List

from .base import SearchableService
from ..core.models import (
    PaginationParams,
    APIResponse,
    Comment,
    CommentSearchParams,
)
from ..events.event_types import CommentEvent, CommentEvents


class CommentsService(SearchableService):
    """评论服务 - 处理所有评论相关的API操作"""
    
    _endpoint_prefix = "comments"
    
    # ==================== 基础CRUD操作 ====================
    
    async def list(
        self,
        post_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        creator_name: Optional[str] = None,
        body_matches: Optional[str] = None,
        is_deleted: Optional[bool] = None,
        is_sticky: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取评论列表
        
        Args:
            post_id: 帖子ID
            creator_id: 创建者ID
            creator_name: 创建者名称
            body_matches: 内容匹配
            is_deleted: 是否已删除
            is_sticky: 是否置顶
            page: 页码
            limit: 每页数量
            order: 排序方式
            **kwargs: 其他搜索参数
        
        Returns:
            评论列表响应
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
        if is_deleted is not None:
            params["search[is_deleted]"] = str(is_deleted).lower()
        if is_sticky is not None:
            params["search[is_sticky]"] = str(is_sticky).lower()
        if order:
            params["search[order]"] = order
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        response = await self._list(params=params, pagination=pagination)
        
        if response.success:
            await self._emit_event(CommentEvent(
                event_type=CommentEvents.SEARCHED,
                post_id=post_id,
            ))
        
        return response
    
    async def get(self, comment_id: int) -> APIResponse:
        """
        获取单个评论
        
        Args:
            comment_id: 评论ID
        
        Returns:
            评论详情响应
        """
        response = await self._get(comment_id)
        
        if response.success:
            await self._emit_event(CommentEvent(
                event_type=CommentEvents.FETCHED,
                comment_id=comment_id,
                comment_data=response.data,
            ))
        
        return response
    
    async def create(
        self,
        post_id: int,
        body: str,
        do_not_bump_post: bool = False,
    ) -> APIResponse:
        """
        创建评论
        
        Args:
            post_id: 帖子ID
            body: 评论内容
            do_not_bump_post: 是否不触发帖子置顶
        
        Returns:
            创建响应
        """
        data = {
            "comment": {
                "post_id": post_id,
                "body": body,
                "do_not_bump_post": do_not_bump_post,
            }
        }
        
        response = await self._create(data)
        
        if response.success:
            await self._emit_event(CommentEvent(
                event_type=CommentEvents.CREATED,
                post_id=post_id,
                comment_data=response.data,
            ))
        
        return response
    
    async def update(
        self,
        comment_id: int,
        body: Optional[str] = None,
        is_sticky: Optional[bool] = None,
    ) -> APIResponse:
        """
        更新评论
        
        Args:
            comment_id: 评论ID
            body: 新内容
            is_sticky: 是否置顶
        
        Returns:
            更新响应
        """
        data = {"comment": {}}
        
        if body is not None:
            data["comment"]["body"] = body
        if is_sticky is not None:
            data["comment"]["is_sticky"] = is_sticky
        
        response = await self._update(comment_id, data)
        
        if response.success:
            await self._emit_event(CommentEvent(
                event_type=CommentEvents.UPDATED,
                comment_id=comment_id,
                comment_data=response.data,
            ))
        
        return response
    
    async def delete(self, comment_id: int) -> APIResponse:
        """
        删除评论
        
        Args:
            comment_id: 评论ID
        
        Returns:
            删除响应
        """
        response = await self._delete(comment_id)
        
        if response.success:
            await self._emit_event(CommentEvent(
                event_type=CommentEvents.DELETED,
                comment_id=comment_id,
            ))
        
        return response
    
    async def undelete(self, comment_id: int) -> APIResponse:
        """
        恢复已删除的评论
        
        Args:
            comment_id: 评论ID
        
        Returns:
            恢复响应
        """
        return await self.client.post(f"comments/{comment_id}/undelete")
    
    # ==================== 投票操作 ====================
    
    async def vote(self, comment_id: int, score: int = 1) -> APIResponse:
        """
        为评论投票
        
        Args:
            comment_id: 评论ID
            score: 分数 (1 为赞, -1 为踩)
        
        Returns:
            投票响应
        """
        data = {"score": score}
        response = await self.client.post(f"comments/{comment_id}/votes", json_data=data)
        
        if response.success:
            await self._emit_event(CommentEvent(
                event_type=CommentEvents.VOTED,
                comment_id=comment_id,
                comment_data={"score": score},
            ))
        
        return response
    
    async def unvote(self, comment_id: int) -> APIResponse:
        """
        取消评论投票
        
        Args:
            comment_id: 评论ID
        
        Returns:
            取消投票响应
        """
        return await self.client.delete(f"comments/{comment_id}/votes")
    
    async def get_votes(
        self,
        comment_id: Optional[int] = None,
        user_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取评论投票列表
        
        Args:
            comment_id: 评论ID
            user_id: 用户ID
            pagination: 分页参数
        
        Returns:
            投票列表响应
        """
        params = {}
        if comment_id:
            params["search[comment_id]"] = comment_id
        if user_id:
            params["search[user_id]"] = user_id
        
        return await self.client.get(
            "comment_votes",
            params=self._apply_pagination(params, pagination)
        )
    
    # ==================== 搜索操作 ====================
    
    async def search(
        self,
        search_params: Optional[CommentSearchParams] = None,
        pagination: Optional[PaginationParams] = None,
        **kwargs
    ) -> APIResponse:
        """
        高级搜索评论
        
        Args:
            search_params: 搜索参数对象
            pagination: 分页参数
            **kwargs: 额外的搜索参数
        
        Returns:
            搜索结果响应
        """
        params = {}
        
        if search_params:
            params.update(search_params.to_params())
        
        for key, value in kwargs.items():
            if value is not None:
                if not key.startswith("search["):
                    params[f"search[{key}]"] = value
                else:
                    params[key] = value
        
        return await self.client.get(
            "comments/search",
            params=self._apply_pagination(params, pagination)
        )
    
    # ==================== 工具方法 ====================
    
    def parse_comment(self, data: Dict[str, Any]) -> Comment:
        """解析评论数据"""
        return Comment.from_dict(data)
    
    def parse_comments(self, data: List[Dict[str, Any]]) -> List[Comment]:
        """解析评论列表"""
        return [Comment.from_dict(item) for item in data]
    
    async def get_parsed(self, comment_id: int) -> Optional[Comment]:
        """获取并解析评论"""
        response = await self.get(comment_id)
        if response.success and response.data:
            return self.parse_comment(response.data)
        return None
    
    async def get_by_post(
        self,
        post_id: int,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Comment]:
        """
        获取帖子的所有评论
        
        Args:
            post_id: 帖子ID
            page: 页码
            limit: 每页数量
        
        Returns:
            Comment对象列表
        """
        response = await self.list(post_id=post_id, page=page, limit=limit)
        if response.success and isinstance(response.data, list):
            return self.parse_comments(response.data)
        return []