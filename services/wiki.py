"""
Danbooru API Plugin - Wiki 服务
Wiki页面相关的所有API操作
"""

from typing import Optional, Dict, Any, List

from .base import VersionedService
from core.models import (
    PaginationParams,
    APIResponse,
    WikiPage,
    WikiSearchParams,
)
from events.event_types import WikiEvent, WikiEvents


class WikiService(VersionedService):
    """Wiki服务 - 处理所有Wiki页面相关的API操作"""
    
    _endpoint_prefix = "wiki_pages"
    _versions_endpoint = "wiki_page_versions"
    
    # ==================== 基础CRUD操作 ====================
    
    async def list(
        self,
        title: Optional[str] = None,
        title_matches: Optional[str] = None,
        body_matches: Optional[str] = None,
        creator_id: Optional[int] = None,
        is_locked: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        hide_deleted: bool = True,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取Wiki页面列表
        
        Args:
            title: 精确匹配标题
            title_matches: 标题匹配（支持通配符*）
            body_matches: 内容匹配
            creator_id: 创建者ID
            is_locked: 是否锁定
            is_deleted: 是否已删除
            hide_deleted: 是否隐藏已删除
            page: 页码
            limit: 每页数量
            order: 排序方式
            **kwargs: 其他搜索参数
        
        Returns:
            Wiki页面列表响应
        """
        params = {}
        
        if title:
            params["search[title]"] = title
        if title_matches:
            params["search[title_matches]"] = title_matches
        if body_matches:
            params["search[body_matches]"] = body_matches
        if creator_id:
            params["search[creator_id]"] = creator_id
        if is_locked is not None:
            params["search[is_locked]"] = str(is_locked).lower()
        if is_deleted is not None:
            params["search[is_deleted]"] = str(is_deleted).lower()
        if hide_deleted:
            params["search[hide_deleted]"] = "true"
        if order:
            params["search[order]"] = order
        
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        response = await self._list(params=params, pagination=pagination)
        
        if response.success:
            await self._emit_event(WikiEvent(
                event_type=WikiEvents.SEARCHED,
                wiki_title=title_matches or title,
            ))
        
        return response

    async def search(
        self,
        pagination: Optional[PaginationParams] = None,
        **kwargs,
    ) -> APIResponse:
        """使用 /wiki_pages/search 进行搜索"""
        params = {}
        for key, value in kwargs.items():
            if value is not None:
                if not key.startswith("search["):
                    params[f"search[{key}]"] = value
                else:
                    params[key] = value
        return await self.client.get(
            "wiki_pages/search",
            params=self._apply_pagination(params, pagination),
        )
    
    async def get(self, wiki_id: int) -> APIResponse:
        """
        获取单个Wiki页面（按ID）
        
        Args:
            wiki_id: Wiki页面ID
        
        Returns:
            Wiki页面详情响应
        """
        response = await self._get(wiki_id)
        
        if response.success:
            await self._emit_event(WikiEvent(
                event_type=WikiEvents.FETCHED,
                wiki_id=wiki_id,
                wiki_data=response.data,
            ))
        
        return response
    
    async def get_by_title(self, title: str) -> APIResponse:
        """
        获取单个Wiki页面（按标题）
        
        Args:
            title: 页面标题
        
        Returns:
            Wiki页面详情响应
        """
        # Wiki页面可以通过标题直接访问
        response = await self.client.get(f"wiki_pages/{title}")
        
        if response.success:
            await self._emit_event(WikiEvent(
                event_type=WikiEvents.FETCHED,
                wiki_title=title,
                wiki_data=response.data,
            ))
        
        return response

    async def show_or_new(self, title: str) -> APIResponse:
        """显示或准备创建 Wiki 页面"""
        return await self.client.get("wiki_pages/show_or_new", params={"title": title})
    
    async def create(
        self,
        title: str,
        body: str,
        other_names: Optional[List[str]] = None,
        is_locked: bool = False,
    ) -> APIResponse:
        """
        创建Wiki页面
        
        Args:
            title: 标题
            body: 内容
            other_names: 其他名称
            is_locked: 是否锁定
        
        Returns:
            创建响应
        """
        data = {
            "wiki_page": {
                "title": title,
                "body": body,
                "is_locked": is_locked,
            }
        }
        
        if other_names:
            data["wiki_page"]["other_names_string"] = " ".join(other_names)
        
        response = await self._create(data)
        
        if response.success:
            await self._emit_event(WikiEvent(
                event_type=WikiEvents.CREATED,
                wiki_title=title,
                wiki_data=response.data,
            ))
        
        return response
    
    async def update(
        self,
        wiki_id: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        other_names: Optional[List[str]] = None,
        is_locked: Optional[bool] = None,
    ) -> APIResponse:
        """
        更新Wiki页面
        
        Args:
            wiki_id: Wiki页面ID
            title: 新标题
            body: 新内容
            other_names: 其他名称
            is_locked: 是否锁定
        
        Returns:
            更新响应
        """
        data = {"wiki_page": {}}
        
        if title is not None:
            data["wiki_page"]["title"] = title
        if body is not None:
            data["wiki_page"]["body"] = body
        if other_names is not None:
            data["wiki_page"]["other_names_string"] = " ".join(other_names)
        if is_locked is not None:
            data["wiki_page"]["is_locked"] = is_locked
        
        response = await self._update(wiki_id, data)
        
        if response.success:
            await self._emit_event(WikiEvent(
                event_type=WikiEvents.UPDATED,
                wiki_id=wiki_id,
                wiki_data=response.data,
            ))
        
        return response
    
    async def delete(self, wiki_id: int) -> APIResponse:
        """
        删除Wiki页面
        
        Args:
            wiki_id: Wiki页面ID
        
        Returns:
            删除响应
        """
        response = await self._delete(wiki_id)
        
        if response.success:
            await self._emit_event(WikiEvent(
                event_type=WikiEvents.DELETED,
                wiki_id=wiki_id,
            ))
        
        return response

    async def diff_version(
        self,
        version_id: Optional[int] = None,
        **kwargs,
    ) -> APIResponse:
        """获取 Wiki 版本差异"""
        params = {}
        if version_id is not None:
            params["id"] = version_id
        params.update(kwargs)
        return await self.client.get("wiki_page_versions/diff", params=params)

    async def get_version(self, version_id: int) -> APIResponse:
        """获取单个 Wiki 版本"""
        return await self.client.get(f"wiki_page_versions/{version_id}")
    
    # ==================== 版本控制 ====================
    
    async def revert(self, wiki_id: int, version_id: int) -> APIResponse:
        """
        恢复到指定版本
        
        Args:
            wiki_id: Wiki页面ID
            version_id: 版本ID
        
        Returns:
            恢复响应
        """
        data = {"version_id": version_id}
        response = await self.client.put(f"wiki_pages/{wiki_id}/revert", json_data=data)
        
        if response.success:
            await self._emit_event(WikiEvent(
                event_type=WikiEvents.REVERTED,
                wiki_id=wiki_id,
            ))
        
        return response
    
    async def get_versions(
        self,
        wiki_page_id: Optional[int] = None,
        title: Optional[str] = None,
        updater_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取Wiki页面版本历史
        
        Args:
            wiki_page_id: Wiki页面ID
            title: 页面标题
            updater_id: 更新者ID
            pagination: 分页参数
        
        Returns:
            版本列表响应
        """
        params = {}
        
        if wiki_page_id:
            params["search[wiki_page_id]"] = wiki_page_id
        if title:
            params["search[title]"] = title
        if updater_id:
            params["search[updater_id]"] = updater_id
        
        return await self.client.get(
            "wiki_page_versions",
            params=self._apply_pagination(params, pagination)
        )
    
    async def get_version(self, version_id: int) -> APIResponse:
        """
        获取单个版本详情
        
        Args:
            version_id: 版本ID
        
        Returns:
            版本详情响应
        """
        return await self.client.get(f"wiki_page_versions/{version_id}")
    
    async def get_version_diff(
        self,
        version_id: Optional[int] = None,
        thispage: Optional[int] = None,
        otherpage: Optional[int] = None,
    ) -> APIResponse:
        """
        获取版本差异
        
        Args:
            version_id: 当前版本ID
            thispage: 当前版本ID
            otherpage: 对比版本ID
        
        Returns:
            版本差异响应
        """
        params = {}
        if version_id:
            params["version_id"] = version_id
        if thispage:
            params["thispage"] = thispage
        if otherpage:
            params["otherpage"] = otherpage
        
        return await self.client.get("wiki_page_versions/diff", params=params)
    
    # ==================== 搜索操作 ====================
    
    async def search(
        self,
        search_params: Optional[WikiSearchParams] = None,
        pagination: Optional[PaginationParams] = None,
        **kwargs
    ) -> APIResponse:
        """
        高级搜索Wiki页面
        
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
            "wiki_pages/search",
            params=self._apply_pagination(params, pagination)
        )
    
    async def show_or_new(self, title: str) -> APIResponse:
        """
        显示Wiki页面或准备创建新页面
        
        Args:
            title: 页面标题
        
        Returns:
            页面信息或创建表单数据
        """
        return await self.client.get("wiki_pages/show_or_new", params={"title": title})
    
    # ==================== 工具方法 ====================
    
    def parse_wiki(self, data: Dict[str, Any]) -> WikiPage:
        """解析Wiki页面数据"""
        return WikiPage.from_dict(data)
    
    def parse_wikis(self, data: List[Dict[str, Any]]) -> List[WikiPage]:
        """解析Wiki页面列表"""
        return [WikiPage.from_dict(item) for item in data]
    
    async def get_parsed(self, wiki_id: int) -> Optional[WikiPage]:
        """获取并解析Wiki页面"""
        response = await self.get(wiki_id)
        if response.success and response.data:
            return self.parse_wiki(response.data)
        return None
    
    async def find_by_title(self, title: str) -> Optional[WikiPage]:
        """
        按标题查找Wiki页面
        
        Args:
            title: 页面标题
        
        Returns:
            WikiPage对象或None
        """
        response = await self.get_by_title(title)
        if response.success and response.data:
            return self.parse_wiki(response.data)
        return None
