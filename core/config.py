"""
Danbooru API Plugin - 配置管理模块
管理插件配置和API设置
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import os


@dataclass
class APIConfig:
    """API配置"""
    base_url: str = "https://danbooru.donmai.us"
    test_url: str = "https://testbooru.donmai.us"
    use_test_server: bool = False
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_per_second: int = 10  # 全局速率限制
    
    @property
    def active_url(self) -> str:
        """获取当前使用的URL"""
        return self.test_url if self.use_test_server else self.base_url


@dataclass
class AuthConfig:
    """认证配置"""
    username: str = ""
    api_key: str = ""
    
    @property
    def is_configured(self) -> bool:
        """检查认证是否已配置"""
        return bool(self.username and self.api_key)


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl_seconds: int = 300  # 5分钟
    max_size: int = 1000
    cache_posts: bool = True
    cache_tags: bool = True
    cache_artists: bool = True
    cache_users: bool = True


@dataclass
class FilterConfig:
    """内容过滤配置"""
    allowed_ratings: List[str] = field(default_factory=lambda: ["g", "s"])
    blocked_tags: List[str] = field(default_factory=list)
    required_tags: List[str] = field(default_factory=list)
    min_score: Optional[int] = None
    max_results: int = 20


VALID_RATINGS = ("g", "s", "q", "e")


def _normalize_allowed_ratings(value: Any) -> List[str]:
    ratings: List[str] = []
    if isinstance(value, dict):
        for rating in VALID_RATINGS:
            if value.get(rating) is True:
                ratings.append(rating)
    elif isinstance(value, list):
        for item in value:
            if not isinstance(item, str):
                continue
            lowered = item.lower()
            if lowered in VALID_RATINGS:
                ratings.append(lowered)

    if not ratings:
        ratings = ["g", "s"]
    return ratings


@dataclass
class DisplayConfig:
    """显示配置"""
    show_preview: bool = True
    search_limit: int = 1
    only_image: bool = False
    preview_size: str = "preview"  # preview, sample, original
    show_tags: bool = True
    max_tags_display: int = 0
    show_source: bool = True
    show_artist: bool = True
    show_score: bool = True
    language: str = "zh-CN"


@dataclass
class SubscriptionsConfig:
    """订阅配置"""
    enabled: bool = True
    send_interval_minutes: int = 120


@dataclass
class PluginConfig:
    """插件主配置"""
    api: APIConfig = field(default_factory=APIConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    filter: FilterConfig = field(default_factory=FilterConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    subscriptions: SubscriptionsConfig = field(default_factory=SubscriptionsConfig)
    
    # 功能开关
    enable_commands: bool = True
    enable_llm_tools: bool = True
    enable_auto_tag: bool = False
    
    # 调试设置
    debug: bool = False
    log_api_calls: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginConfig':
        """从字典创建配置"""
        config = cls()
        
        if "api" in data:
            api_data = data["api"]
            config.api = APIConfig(
                base_url=api_data.get("base_url", config.api.base_url),
                test_url=api_data.get("test_url", config.api.test_url),
                use_test_server=api_data.get("use_test_server", config.api.use_test_server),
                timeout=api_data.get("timeout", config.api.timeout),
                max_retries=api_data.get("max_retries", config.api.max_retries),
                retry_delay=api_data.get("retry_delay", config.api.retry_delay),
                rate_limit_per_second=api_data.get("rate_limit_per_second", config.api.rate_limit_per_second),
            )
        
        if "auth" in data:
            auth_data = data["auth"]
            config.auth = AuthConfig(
                username=auth_data.get("username", ""),
                api_key=auth_data.get("api_key", ""),
            )
        
        if "cache" in data:
            cache_data = data["cache"]
            config.cache = CacheConfig(
                enabled=cache_data.get("enabled", config.cache.enabled),
                ttl_seconds=cache_data.get("ttl_seconds", config.cache.ttl_seconds),
                max_size=cache_data.get("max_size", config.cache.max_size),
                cache_posts=cache_data.get("cache_posts", config.cache.cache_posts),
                cache_tags=cache_data.get("cache_tags", config.cache.cache_tags),
                cache_artists=cache_data.get("cache_artists", config.cache.cache_artists),
                cache_users=cache_data.get("cache_users", config.cache.cache_users),
            )
        
        if "filter" in data:
            filter_data = data["filter"]
            config.filter = FilterConfig(
                allowed_ratings=_normalize_allowed_ratings(
                    filter_data.get("allowed_ratings", config.filter.allowed_ratings)
                ),
                blocked_tags=filter_data.get("blocked_tags", config.filter.blocked_tags),
                required_tags=filter_data.get("required_tags", config.filter.required_tags),
                min_score=filter_data.get("min_score", config.filter.min_score),
                max_results=filter_data.get("max_results", config.filter.max_results),
            )
        
        if "display" in data:
            display_data = data["display"]
            config.display = DisplayConfig(
                show_preview=display_data.get("show_preview", config.display.show_preview),
                search_limit=display_data.get("search_limit", config.display.search_limit),
                only_image=display_data.get("only_image", config.display.only_image),
                preview_size=display_data.get("preview_size", config.display.preview_size),
                show_tags=display_data.get("show_tags", config.display.show_tags),
                max_tags_display=display_data.get("max_tags_display", config.display.max_tags_display),
                show_source=display_data.get("show_source", config.display.show_source),
                show_artist=display_data.get("show_artist", config.display.show_artist),
                show_score=display_data.get("show_score", config.display.show_score),
                language=display_data.get("language", config.display.language),
            )

        if "subscriptions" in data:
            subs_data = data["subscriptions"]
            send_interval_minutes = subs_data.get("send_interval_minutes")
            config.subscriptions = SubscriptionsConfig(
                enabled=subs_data.get("enabled", config.subscriptions.enabled),
                send_interval_minutes=send_interval_minutes
                if send_interval_minutes is not None
                else config.subscriptions.send_interval_minutes,
            )
        
        # 功能开关
        config.enable_commands = data.get("enable_commands", config.enable_commands)
        config.enable_llm_tools = data.get("enable_llm_tools", config.enable_llm_tools)
        config.enable_auto_tag = data.get("enable_auto_tag", config.enable_auto_tag)
        
        # 调试设置
        config.debug = data.get("debug", config.debug)
        config.log_api_calls = data.get("log_api_calls", config.log_api_calls)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "api": {
                "base_url": self.api.base_url,
                "test_url": self.api.test_url,
                "use_test_server": self.api.use_test_server,
                "timeout": self.api.timeout,
                "max_retries": self.api.max_retries,
                "retry_delay": self.api.retry_delay,
                "rate_limit_per_second": self.api.rate_limit_per_second,
            },
            "auth": {
                "username": self.auth.username,
                "api_key": self.auth.api_key,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "ttl_seconds": self.cache.ttl_seconds,
                "max_size": self.cache.max_size,
                "cache_posts": self.cache.cache_posts,
                "cache_tags": self.cache.cache_tags,
                "cache_artists": self.cache.cache_artists,
                "cache_users": self.cache.cache_users,
            },
            "filter": {
                "allowed_ratings": {
                    "g": "g" in self.filter.allowed_ratings,
                    "s": "s" in self.filter.allowed_ratings,
                    "q": "q" in self.filter.allowed_ratings,
                    "e": "e" in self.filter.allowed_ratings,
                },
                "blocked_tags": self.filter.blocked_tags,
                "required_tags": self.filter.required_tags,
                "min_score": self.filter.min_score,
                "max_results": self.filter.max_results,
            },
            "display": {
                "show_preview": self.display.show_preview,
                "search_limit": self.display.search_limit,
                "only_image": self.display.only_image,
                "preview_size": self.display.preview_size,
                "show_tags": self.display.show_tags,
                "max_tags_display": self.display.max_tags_display,
                "show_source": self.display.show_source,
                "show_artist": self.display.show_artist,
                "show_score": self.display.show_score,
                "language": self.display.language,
            },
            "subscriptions": {
                "enabled": self.subscriptions.enabled,
                "send_interval_minutes": self.subscriptions.send_interval_minutes,
            },
            "enable_commands": self.enable_commands,
            "enable_llm_tools": self.enable_llm_tools,
            "enable_auto_tag": self.enable_auto_tag,
            "debug": self.debug,
            "log_api_calls": self.log_api_calls,
        }
    
    def validate(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 验证API配置
        if not self.api.base_url:
            errors.append("API base_url不能为空")
        
        if self.api.timeout <= 0:
            errors.append("API timeout必须大于0")
        
        if self.api.max_retries < 0:
            errors.append("API max_retries不能为负数")
        
        # 验证过滤配置
        valid_ratings = {"g", "s", "q", "e"}
        for rating in self.filter.allowed_ratings:
            if rating not in valid_ratings:
                errors.append(f"无效的rating值: {rating}")
        
        if self.filter.max_results <= 0 or self.filter.max_results > 200:
            errors.append("max_results必须在1-200之间")

        if self.display.search_limit <= 0 or self.display.search_limit > 20:
            errors.append("display.search_limit必须在1-20之间")

        if self.subscriptions.tag_poll_minutes <= 0:
            errors.append("subscriptions.tag_poll_minutes必须大于0")

        if self.subscriptions.send_interval_minutes < 0:
            errors.append("subscriptions.send_interval_minutes不能为负数")
        
        # 验证缓存配置
        if self.cache.ttl_seconds < 0:
            errors.append("cache ttl_seconds不能为负数")
        
        if self.cache.max_size <= 0:
            errors.append("cache max_size必须大于0")
        
        return errors

    def resolve_batch_limit(
        self,
        requested: Optional[int],
        default: int,
        hard_cap: int,
    ) -> int:
        """统一批量命令的 limit 规则。"""
        limit = requested if requested is not None else default
        if limit <= 0:
            limit = default if default > 0 else 1
        limit = min(limit, hard_cap)
        if self.display.search_limit > 0:
            limit = min(limit, self.display.search_limit)
        return limit


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: Optional[PluginConfig] = None
    
    @property
    def config(self) -> PluginConfig:
        """获取配置实例"""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def load(self) -> PluginConfig:
        """加载配置"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return PluginConfig.from_dict(data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载配置失败: {e}")
        
        return PluginConfig()
    
    def save(self) -> bool:
        """保存配置"""
        if not self.config_path:
            return False
        
        try:
            # 确保目录存在
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"保存配置失败: {e}")
            return False
    
    def update(self, **kwargs) -> bool:
        """更新配置"""
        current_dict = self.config.to_dict()
        
        for key, value in kwargs.items():
            if "." in key:
                # 支持嵌套键，如 "api.timeout"
                parts = key.split(".")
                target = current_dict
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = value
            else:
                current_dict[key] = value
        
        self._config = PluginConfig.from_dict(current_dict)
        return self.save()
    
    def reset(self) -> PluginConfig:
        """重置为默认配置"""
        self._config = PluginConfig()
        self.save()
        return self._config
    
    def validate(self) -> List[str]:
        """验证当前配置"""
        return self.config.validate()
