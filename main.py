"""
Danbooru API Plugin for AstrBot
完整的 Danbooru API 封装插件，使用微服务+事件驱动架构

Features:
- 完整的 Danbooru API 支持
- 微服务架构设计
- 事件驱动通信
- 完善的错误处理
- 详细的帮助信息
"""

import os
import sys

# Ensure plugin root is on sys.path for absolute imports like "core.*"
sys.path.append(os.path.dirname(__file__))

from typing import Optional, Dict, Any
import traceback

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from core.client import DanbooruClient
from core.config import PluginConfig
from core.exceptions import (
    DanbooruError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ForbiddenError,
    ValidationError,
)
from events.event_bus import EventBus
from services.registry import ServiceRegistry
from commands import HELP_MESSAGES, CommandContext, CommandParser, build_handlers


@register("danbooru", "AstrBot", "Danbooru API 完整封装插件", "1.0.0")
class DanbooruPlugin(Star):
    """Danbooru API 插件主类"""

    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.context = context
        self.plugin_config = config or {}

        self.config: Optional[PluginConfig] = None
        self.client: Optional[DanbooruClient] = None
        self.event_bus: Optional[EventBus] = None
        self.services: Optional[ServiceRegistry] = None
        self.handlers: Dict[str, Any] = {}
        self.parser = CommandParser()

    async def initialize(self):
        """插件初始化"""
        logger.info("正在初始化 Danbooru 插件...")

        try:
            self.config = PluginConfig.from_dict(self.plugin_config)

            self.event_bus = EventBus.get_instance()
            await self.event_bus.start()

            self.client = DanbooruClient(
                config=self.config,
                event_bus=self.event_bus,
            )

            self.services = ServiceRegistry.build(self.client, self.event_bus)
            ctx = CommandContext(
                client=self.client,
                config=self.config,
                services=self.services,
                help_messages=HELP_MESSAGES,
                parser=self.parser,
            )
            self.handlers = build_handlers(ctx)

            logger.info("Danbooru 插件初始化完成")

        except Exception as e:
            logger.error(f"Danbooru 插件初始化失败: {e}")
            logger.error(traceback.format_exc())

    async def terminate(self):
        """插件销毁"""
        logger.info("正在关闭 Danbooru 插件...")

        try:
            if self.event_bus:
                await self.event_bus.stop()

            if self.client:
                await self.client.close()

            logger.info("Danbooru 插件已关闭")

        except Exception as e:
            logger.error(f"Danbooru 插件关闭时出错: {e}")

    async def _handle_error(self, event: AstrMessageEvent, error: Exception):
        """统一错误处理"""
        if isinstance(error, AuthenticationError):
            yield event.plain_result("❌ 认证失败：请检查API密钥配置")
        elif isinstance(error, RateLimitError):
            yield event.plain_result(
                f"⏳ 请求过于频繁，请稍后再试（{error.retry_after}秒后）"
            )
        elif isinstance(error, NotFoundError):
            yield event.plain_result("❌ 未找到请求的资源")
        elif isinstance(error, ForbiddenError):
            yield event.plain_result("🚫 没有权限执行此操作")
        elif isinstance(error, ValidationError):
            yield event.plain_result(f"❌ 参数错误：{error.message}")
        elif isinstance(error, DanbooruError):
            yield event.plain_result(f"❌ API错误：{error.message}")
        else:
            logger.error(f"未知错误: {error}")
            logger.error(traceback.format_exc())
            yield event.plain_result(f"❌ 发生错误：{str(error)}")

    def _finalize_result(self, event: AstrMessageEvent, result):
        return result

    @filter.command("danbooru")
    async def cmd_main(self, event: AstrMessageEvent):
        """Danbooru 主命令入口"""
        message = event.message_str.strip()
        parts = message.split(maxsplit=2)

        if len(parts) <= 1:
            yield event.plain_result(HELP_MESSAGES["main"])
            return

        if self.config and not self.config.enable_commands:
            yield event.plain_result("❌ 当前配置已禁用命令功能")
            return

        if not self.handlers:
            yield event.plain_result("❌ 命令未初始化，请稍后再试")
            return

        sub_cmd = parts[1].lower() if len(parts) > 1 else ""
        args = parts[2] if len(parts) > 2 else ""

        handler = self.handlers.get(sub_cmd)
        if handler:
            try:
                async for result in handler(event, args):
                    yield self._finalize_result(event, result)
            except Exception as e:
                async for result in self._handle_error(event, e):
                    yield result
        else:
            tag_query = " ".join(part for part in [sub_cmd, args] if part).strip()
            posts_handler = self.handlers.get("posts") if self.handlers else None
            if posts_handler and tag_query:
                try:
                    async for result in posts_handler(event, tag_query):
                        yield self._finalize_result(event, result)
                    return
                except Exception as e:
                    async for result in self._handle_error(event, e):
                        yield result
                    return

            yield event.plain_result(
                f"❌ 未知命令: {sub_cmd}\n\n使用 `/danbooru help` 查看帮助"
            )
