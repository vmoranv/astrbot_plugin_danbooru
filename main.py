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
import asyncio
from datetime import datetime

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
from commands.handlers.posts import (
    _apply_filters,
    _build_image_chain,
    _build_text_image_chain,
    _is_image_accessible,
    _select_image_url,
)


@register("danbooru", "AstrBot", "Danbooru API 完整封装插件", "1.0.1")
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
        self.command_ctx: Optional[CommandContext] = None
        self._subscription_tasks: list[asyncio.Task] = []
        self._subscription_stop: Optional[asyncio.Event] = None

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
            self.command_ctx = ctx
            self.handlers = build_handlers(ctx)

            self._start_subscriptions()
            logger.info("Danbooru 插件初始化完成")

        except Exception as e:
            logger.error(f"Danbooru 插件初始化失败: {e}")
            logger.error(traceback.format_exc())

    async def terminate(self):
        """插件销毁"""
        logger.info("正在关闭 Danbooru 插件...")

        try:
            await self._stop_subscriptions()
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

    def _start_subscriptions(self) -> None:
        if not self.config or not self.config.subscriptions.enabled:
            return
        if self._subscription_tasks:
            return
        self._subscription_stop = asyncio.Event()
        self._subscription_tasks = [
            asyncio.create_task(self._run_subscription_cycle()),
        ]

    async def _stop_subscriptions(self) -> None:
        if self._subscription_stop:
            self._subscription_stop.set()
        for task in self._subscription_tasks:
            task.cancel()
        if self._subscription_tasks:
            await asyncio.gather(*self._subscription_tasks, return_exceptions=True)
        self._subscription_tasks = []
        self._subscription_stop = None

    async def _sleep_or_stop(self, seconds: float) -> bool:
        if not self._subscription_stop:
            await asyncio.sleep(seconds)
            return False
        try:
            await asyncio.wait_for(self._subscription_stop.wait(), timeout=seconds)
            return True
        except asyncio.TimeoutError:
            return False

    def _get_search_limit(self, fallback: int = 5) -> int:
        if self.config and self.config.display.search_limit > 0:
            return self.config.display.search_limit
        return fallback

    async def _send_chain(self, session: str, chain: MessageEventResult) -> None:
        try:
            await self.context.send_message(session, chain)
        except Exception as exc:
            logger.error(f"订阅消息发送失败: {exc}")

    async def _dispatch_tag_subscriptions(self) -> None:
        if not self.services or not self.command_ctx or not self.config:
            return
        groups = await self.services.subscriptions.list_groups()
        limit = min(self._get_search_limit(), 20)
        only_image = bool(self.config.display.only_image)
        show_preview = bool(self.config.display.show_preview)

        for group_id, group in groups.items():
            session = group.get("session_id")
            if not session:
                continue
            tags_map = group.get("tags", {})
            for tag, meta in tags_map.items():
                last_id = meta.get("last_post_id") if isinstance(meta, dict) else None
                query = _apply_filters(self.command_ctx, tag)
                tokens = query.split() if query else [tag]
                tokens.append("order:id_desc")
                if last_id:
                    tokens.append(f"id:>{last_id}")
                tag_query = " ".join(tokens)

                response = await self.services.posts.list(tags=tag_query, limit=limit)
                if not response.success or not response.data:
                    continue

                posts = response.data
                max_id = max((post.get("id", 0) for post in posts), default=0)

                if show_preview or only_image:
                    selected: list[tuple[dict, str]] = []
                    for post in posts:
                        url = _select_image_url(self.command_ctx, post)
                        if not url:
                            continue
                        if not await _is_image_accessible(self.command_ctx, url):
                            continue
                        selected.append((post, url))
                        if len(selected) >= limit:
                            break
                    if selected:
                        if only_image:
                            chain = _build_image_chain([url for _, url in selected])
                            if chain:
                                await self._send_chain(session, chain)
                        else:
                            for post, url in reversed(selected):
                                score = post.get("score", 0)
                                fav = post.get("fav_count", 0)
                                rating = post.get("rating", "?")
                                text = (
                                    f"🔔 订阅更新: {tag}\n"
                                    f"#{post['id']} | ⭐{score} ❤️{fav} | {rating}\n"
                                    f"🔗 https://danbooru.donmai.us/posts/{post['id']}"
                                )
                                chain = _build_text_image_chain(text, url)
                                if chain:
                                    await self._send_chain(session, chain)
                    if max_id:
                        await self.services.subscriptions.update_last_post(group_id, tag, int(max_id))
                else:
                    for post in reversed(posts[:limit]):
                        score = post.get("score", 0)
                        fav = post.get("fav_count", 0)
                        rating = post.get("rating", "?")
                        text = (
                            f"🔔 订阅更新: {tag}\n"
                            f"#{post['id']} | ⭐{score} ❤️{fav} | {rating}\n"
                            f"🔗 https://danbooru.donmai.us/posts/{post['id']}"
                        )
                        await self._send_chain(session, MessageEventResult().message(text))
                    if max_id:
                        await self.services.subscriptions.update_last_post(group_id, tag, int(max_id))

    async def _dispatch_popular_subscriptions(self) -> None:
        if not self.services or not self.command_ctx or not self.config:
            return
        groups = await self.services.subscriptions.list_groups()
        limit = min(self._get_search_limit(), 20)
        only_image = bool(self.config.display.only_image)
        show_preview = bool(self.config.display.show_preview)
        now_ts = int(datetime.now().timestamp())
        interval_minutes = max(int(self.config.subscriptions.send_interval_minutes), 1)
        cooldown_seconds = interval_minutes * 60

        groups_by_scale: dict[str, list[tuple[str, str]]] = {}
        for group_id, group in groups.items():
            session = group.get("session_id")
            popular_cfg = group.get("popular", {})
            if not session or not popular_cfg or not popular_cfg.get("enabled"):
                continue
            last_sent = int(popular_cfg.get("last_sent") or 0)
            if last_sent and now_ts - last_sent < cooldown_seconds:
                continue
            scale = str(popular_cfg.get("scale") or "day").lower()
            if scale not in {"day", "week", "month"}:
                scale = "day"
            groups_by_scale.setdefault(scale, []).append((group_id, session))

        if not groups_by_scale:
            return

        for scale, entries in groups_by_scale.items():
            response = await self.services.explore.popular(scale=scale)
            if not response.success or not response.data:
                continue
            posts = response.data

            if show_preview or only_image:
                selected: list[tuple[dict, str]] = []
                for post in posts:
                    url = _select_image_url(self.command_ctx, post)
                    if not url:
                        continue
                    if not await _is_image_accessible(self.command_ctx, url):
                        continue
                    selected.append((post, url))
                    if len(selected) >= limit:
                        break

                if not selected:
                    for group_id, _ in entries:
                        await self.services.subscriptions.update_popular_sent(group_id, now_ts)
                    continue

                urls = [url for _, url in selected]
                total = len(selected)
                for group_id, session in entries:
                    if only_image:
                        chain = _build_image_chain(urls)
                        if chain:
                            await self._send_chain(session, chain)
                    else:
                        for idx, (post, url) in enumerate(selected, 1):
                            score = post.get("score", 0)
                            fav = post.get("fav_count", 0)
                            rating = post.get("rating", "?")
                            text = (
                                f"🔥 热门订阅 ({scale}，第{idx}/{total}条)\n"
                                f"#{post['id']} | ⭐{score} ❤️{fav} | {rating}\n"
                                f"🔗 https://danbooru.donmai.us/posts/{post['id']}"
                            )
                            chain = _build_text_image_chain(text, url)
                            if chain:
                                await self._send_chain(session, chain)
                    await self.services.subscriptions.update_popular_sent(group_id, now_ts)
            else:
                result_lines = [f"🔥 热门订阅 ({scale})\n"]
                for idx, post in enumerate(posts[:limit], 1):
                    score = post.get("score", 0)
                    fav = post.get("fav_count", 0)
                    result_lines.append(f"{idx}. #{post['id']} | ⭐{score} ❤️{fav}")

                text = "\n".join(result_lines)
                for group_id, session in entries:
                    await self._send_chain(session, MessageEventResult().message(text))
                    await self.services.subscriptions.update_popular_sent(group_id, now_ts)

    async def _run_subscription_cycle(self) -> None:
        while True:
            if self._subscription_stop and self._subscription_stop.is_set():
                break
            try:
                await self._dispatch_tag_subscriptions()
                await self._dispatch_popular_subscriptions()
            except Exception as exc:
                logger.error(f"标签订阅处理失败: {exc}")
            interval = 120
            if self.config:
                interval = max(int(self.config.subscriptions.send_interval_minutes), 1)
            if await self._sleep_or_stop(interval * 60):
                break

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
