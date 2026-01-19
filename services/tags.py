"""
Danbooru API Plugin - Tags 服务
标签相关的所有API操作
"""

from typing import Optional, Dict, Any, List, Union

from .base import SearchableService
from core.models import (
    PaginationParams,
    APIResponse,
    Tag,
    TagSearchParams,
    TagCategory,
)
from events.event_types import TagSearchedEvent, TagEvent, TagEvents


class TagsService(SearchableService):
    """标签服务 - 处理所有标签相关的API操作"""
    
    _endpoint_prefix = "tags"
    
    # ==================== 基础CRUD操作 ====================
    
    async def list(
        self,
        name_matches: Optional[str] = None,
        category: Optional[Union[int, TagCategory]] = None,
        hide_empty: bool = False,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        **kwargs
    ) -> APIResponse:
        """
        获取标签列表
        
        Args:
            name_matches: 标签名匹配（支持通配符*）
            category: 标签类别（0=general, 1=artist, 3=copyright, 4=character, 5=meta）
            hide_empty: 是否隐藏无帖子的标签
            page: 页码
            limit: 每页数量
            order: 排序方式
            **kwargs: 其他搜索参数
        
        Returns:
            标签列表响应
        
        Example:
            # 搜索以'touhou'开头的标签
            tags = await tags_service.list(name_matches="touhou*")
            
            # 获取所有角色标签
            tags = await tags_service.list(category=TagCategory.CHARACTER)
        """
        params = {}
        
        if name_matches:
            params["search[name_matches]"] = name_matches
        
        if category is not None:
            cat_value = category.value if isinstance(category, TagCategory) else category
            params["search[category]"] = cat_value
        
        if hide_empty:
            params["search[hide_empty]"] = "true"
        
        if order:
            params["search[order]"] = order
        
        # 添加其他搜索参数
        for key, value in kwargs.items():
            if value is not None:
                params[f"search[{key}]"] = value
        
        pagination = PaginationParams(page=page, limit=limit)
        
        response = await self._list(params=params, pagination=pagination)
        
        if response.success:
            await self._emit_event(TagSearchedEvent(
                query=name_matches or "",
                results_count=len(response.data) if isinstance(response.data, list) else 0,
            ))
        
        return response
    
    async def get(self, tag_id: int) -> APIResponse:
        """
        获取单个标签
        
        Args:
            tag_id: 标签ID
        
        Returns:
            标签详情响应
        """
        response = await self._get(tag_id)
        
        if response.success:
            await self._emit_event(TagEvent(
                event_type=TagEvents.FETCHED,
                tag_id=tag_id,
                tag_data=response.data,
            ))
        
        return response
    
    async def create(
        self,
        name: str,
        category: Optional[Union[int, TagCategory]] = None,
    ) -> APIResponse:
        """
        创建标签
        
        Args:
            name: 标签名
            category: 标签类别
        
        Returns:
            创建响应
        """
        data = {
            "tag": {
                "name": name,
            }
        }
        
        if category is not None:
            data["tag"]["category"] = category.value if isinstance(category, TagCategory) else category
        
        response = await self._create(data)
        
        if response.success:
            await self._emit_event(TagEvent(
                event_type=TagEvents.CREATED,
                tag_name=name,
                tag_data=response.data,
            ))
        
        return response
    
    async def update(
        self,
        tag_id: int,
        category: Optional[Union[int, TagCategory]] = None,
        is_deprecated: Optional[bool] = None,
    ) -> APIResponse:
        """
        更新标签
        
        Args:
            tag_id: 标签ID
            category: 新类别
            is_deprecated: 是否废弃
        
        Returns:
            更新响应
        """
        data = {"tag": {}}
        
        if category is not None:
            data["tag"]["category"] = category.value if isinstance(category, TagCategory) else category
        
        if is_deprecated is not None:
            data["tag"]["is_deprecated"] = is_deprecated
        
        response = await self._update(tag_id, data)
        
        if response.success:
            await self._emit_event(TagEvent(
                event_type=TagEvents.UPDATED,
                tag_id=tag_id,
                tag_data=response.data,
            ))
        
        return response
    
    # ==================== 搜索操作 ====================
    
    async def search(
        self,
        search_params: Optional[TagSearchParams] = None,
        pagination: Optional[PaginationParams] = None,
        **kwargs
    ) -> APIResponse:
        """
        高级搜索标签
        
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
        
        return await self._list(params=params, pagination=pagination)
    
    async def search_by_name(
        self,
        name: str,
        exact: bool = False,
    ) -> APIResponse:
        """
        按名称搜索标签
        
        Args:
            name: 标签名
            exact: 是否精确匹配
        
        Returns:
            搜索结果
        """
        if exact:
            params = {"search[name]": name}
        else:
            # 使用通配符模糊匹配
            params = {"search[name_matches]": f"*{name}*"}
        
        return await self._list(params=params)
    
    # ==================== 标签别名操作 ====================
    
    async def get_aliases(
        self,
        antecedent_name: Optional[str] = None,
        consequent_name: Optional[str] = None,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取标签别名列表
        
        Args:
            antecedent_name: 原标签名
            consequent_name: 目标标签名
            status: 状态
            pagination: 分页参数
        
        Returns:
            别名列表响应
        """
        params = {}
        
        if antecedent_name:
            params["search[antecedent_name]"] = antecedent_name
        if consequent_name:
            params["search[consequent_name]"] = consequent_name
        if status:
            params["search[status]"] = status
        
        return await self.client.get(
            "tag_aliases",
            params=self._apply_pagination(params, pagination)
        )
    
    async def get_alias(self, alias_id: int) -> APIResponse:
        """
        获取单个标签别名
        
        Args:
            alias_id: 别名ID
        
        Returns:
            别名详情响应
        """
        return await self.client.get(f"tag_aliases/{alias_id}")
    
    async def delete_alias(self, alias_id: int) -> APIResponse:
        """
        删除标签别名
        
        Args:
            alias_id: 别名ID
        
        Returns:
            删除响应
        """
        return await self.client.delete(f"tag_aliases/{alias_id}")
    
    # ==================== 标签蕴含操作 ====================
    
    async def get_implications(
        self,
        antecedent_name: Optional[str] = None,
        consequent_name: Optional[str] = None,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> APIResponse:
        """
        获取标签蕴含列表
        
        Args:
            antecedent_name: 原标签名
            consequent_name: 蕴含标签名
            status: 状态
            pagination: 分页参数
        
        Returns:
            蕴含列表响应
        """
        params = {}
        
        if antecedent_name:
            params["search[antecedent_name]"] = antecedent_name
        if consequent_name:
            params["search[consequent_name]"] = consequent_name
        if status:
            params["search[status]"] = status
        
        return await self.client.get(
            "tag_implications",
            params=self._apply_pagination(params, pagination)
        )
    
    async def get_implication(self, implication_id: int) -> APIResponse:
        """
        获取单个标签蕴含
        
        Args:
            implication_id: 蕴含ID
        
        Returns:
            蕴含详情响应
        """
        return await self.client.get(f"tag_implications/{implication_id}")
    
    async def delete_implication(self, implication_id: int) -> APIResponse:
        """
        删除标签蕴含
        
        Args:
            implication_id: 蕴含ID
        
        Returns:
            删除响应
        """
        return await self.client.delete(f"tag_implications/{implication_id}")
    
    # ==================== 相关标签操作 ====================
    
    async def get_related(
        self,
        query: str,
        category: Optional[Union[int, TagCategory]] = None,
    ) -> APIResponse:
        """
        获取相关标签
        
        Args:
            query: 查询标签
            category: 限制类别
        
        Returns:
            相关标签响应
        """
        params = {"query": query}
        
        if category is not None:
            cat_value = category.value if isinstance(category, TagCategory) else category
            params["category"] = cat_value
        
        return await self.client.get("related_tag", params=params)
    
    # ==================== 工具方法 ====================
    
    def parse_tag(self, data: Dict[str, Any]) -> Tag:
        """
        解析标签数据
        
        Args:
            data: 原始数据字典
        
        Returns:
            Tag对象
        """
        return Tag.from_dict(data)
    
    def parse_tags(self, data: List[Dict[str, Any]]) -> List[Tag]:
        """
        解析标签列表
        
        Args:
            data: 原始数据列表
        
        Returns:
            Tag对象列表
        """
        return [Tag.from_dict(item) for item in data]
    
    async def get_parsed(self, tag_id: int) -> Optional[Tag]:
        """
        获取并解析标签
        
        Args:
            tag_id: 标签ID
        
        Returns:
            Tag对象或None
        """
        response = await self.get(tag_id)
        if response.success and response.data:
            return self.parse_tag(response.data)
        return None
    
    async def list_parsed(
        self,
        name_matches: Optional[str] = None,
        category: Optional[Union[int, TagCategory]] = None,
        **kwargs
    ) -> List[Tag]:
        """
        获取并解析标签列表
        
        Args:
            name_matches: 标签名匹配
            category: 标签类别
        
        Returns:
            Tag对象列表
        """
        response = await self.list(name_matches=name_matches, category=category, **kwargs)
        if response.success and isinstance(response.data, list):
            return self.parse_tags(response.data)
        return []
    
    @staticmethod
    def get_category_name(category: int) -> str:
        """
        获取类别名称
        
        Args:
            category: 类别ID
        
        Returns:
            类别名称
        """
        category_names = {
            0: "general",
            1: "artist",
            3: "copyright",
            4: "character",
            5: "meta",
        }
        return category_names.get(category, "unknown")
    
    @staticmethod
    def get_category_color(category: int) -> str:
        """
        获取类别颜色
        
        Args:
            category: 类别ID
        
        Returns:
            颜色代码
        """
        category_colors = {
            0: "#0075f8",  # general - blue
            1: "#c00004",  # artist - red
            3: "#a800aa",  # copyright - purple
            4: "#00ab2c",  # character - green
            5: "#fd9200",  # meta - orange
        }
        return category_colors.get(category, "#888888")