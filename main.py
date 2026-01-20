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

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger

from .core.client import DanbooruClient
from .core.config import PluginConfig
from .core.exceptions import (
    DanbooruError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ForbiddenError,
    ValidationError,
)
from .events.event_bus import EventBus
from .services.registry import ServiceRegistry
from .commands import HELP_MESSAGES, CommandContext, CommandParser, build_handlers
from .commands.handlers.posts import (
    _apply_filters,
    _build_image_chain,
    _build_text_image_chain,
    _format_tags,
    _is_image_accessible,
    _select_image_url,
)


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
        detail = getattr(error, "message", str(error))
        if isinstance(error, AuthenticationError):
            logger.error(f"认证失败: {detail}")
            yield event.plain_result("❌ 认证失败：请检查API密钥配置")
        elif isinstance(error, RateLimitError):
            logger.warning(f"请求过于频繁: {detail}")
            yield event.plain_result(
                f"⏳ 请求过于频繁，请稍后再试（{error.retry_after}秒后）"
            )
        elif isinstance(error, NotFoundError):
            logger.error(f"资源未找到: {detail}")
            yield event.plain_result("❌ 未找到请求的资源")
        elif isinstance(error, ForbiddenError):
            logger.error(f"权限不足: {detail}")
            yield event.plain_result("🚫 没有权限执行此操作")
        elif isinstance(error, ValidationError):
            logger.error(f"参数错误: {detail}")
            yield event.plain_result(f"❌ 参数错误：{detail}")
        elif isinstance(error, DanbooruError):
            logger.error(f"API错误: {detail}")
            yield event.plain_result(f"❌ API错误：{detail}")
        else:
            logger.error(f"未知错误: {detail}")
            logger.error(traceback.format_exc())
            yield event.plain_result(f"❌ 发生错误：{detail}")

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

    async def _send_chain(self, session: str, chain: MessageEventResult) -> bool:
        try:
            await self.context.send_message(session, chain)
            return True
        except Exception as exc:
            logger.error(f"订阅消息发送失败: {exc}")
            return False

    async def _dispatch_tag_subscriptions(self, round_id: int) -> None:
        if not self.services or not self.command_ctx or not self.config:
            return
        groups = await self.services.subscriptions.list_groups()
        limit = min(self._get_search_limit(), 20)
        only_image = bool(self.config.display.only_image)
        show_preview = bool(self.config.display.show_preview)
        dedupe_rounds = max(int(self.config.subscriptions.dedupe_rounds), 0)

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
                sent_ids: list[int] = []

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
                        post_ids = [post.get("id") for post, _ in selected]
                        new_ids = await self.services.subscriptions.filter_new_post_ids(
                            group_id,
                            post_ids,
                            round_id,
                            dedupe_rounds,
                        )
                        if not new_ids:
                            selected = []
                        else:
                            selected = [
                                item
                                for item in selected
                                if item[0].get("id") in new_ids
                            ]
                    if selected:
                        if only_image:
                            chain = _build_image_chain([url for _, url in selected])
                            if chain and await self._send_chain(session, chain):
                                sent_ids.extend(
                                    [
                                        int(post.get("id"))
                                        for post, _ in selected
                                        if post.get("id") is not None
                                    ]
                                )
                        else:
                            for post, url in reversed(selected):
                                score = post.get("score", 0)
                                fav = post.get("fav_count", 0)
                                rating = post.get("rating", "?")
                                tags_text = _format_tags(
                                    self.command_ctx,
                                    post.get("tag_string", ""),
                                )
                                lines = [
                                    f"🔔 订阅更新: {tag}",
                                    f"#{post['id']} | ⭐{score} ❤️{fav} | {rating}",
                                ]
                                if tags_text:
                                    lines.append(f"🏷️ 标签: {tags_text}")
                                lines.append(
                                    f"🔗 https://danbooru.donmai.us/posts/{post['id']}"
                                )
                                text = "\n".join(lines)
                                chain = _build_text_image_chain(text, url)
                                if chain and await self._send_chain(session, chain):
                                    post_id = post.get("id")
                                    if post_id is not None:
                                        sent_ids.append(int(post_id))
                    if sent_ids:
                        await self.services.subscriptions.mark_sent_post_ids(
                            group_id,
                            sent_ids,
                            round_id,
                            dedupe_rounds,
                        )
                    if max_id:
                        await self.services.subscriptions.update_last_post(group_id, tag, int(max_id))
                else:
                    post_ids = [post.get("id") for post in posts[:limit]]
                    new_ids = await self.services.subscriptions.filter_new_post_ids(
                        group_id,
                        post_ids,
                        round_id,
                        dedupe_rounds,
                    )
                    filtered_posts = [
                        post for post in posts[:limit] if post.get("id") in new_ids
                    ]
                    for post in reversed(filtered_posts):
                        score = post.get("score", 0)
                        fav = post.get("fav_count", 0)
                        rating = post.get("rating", "?")
                        tags_text = _format_tags(
                            self.command_ctx,
                            post.get("tag_string", ""),
                        )
                        lines = [
                            f"🔔 订阅更新: {tag}",
                            f"#{post['id']} | ⭐{score} ❤️{fav} | {rating}",
                        ]
                        if tags_text:
                            lines.append(f"🏷️ 标签: {tags_text}")
                        lines.append(
                            f"🔗 https://danbooru.donmai.us/posts/{post['id']}"
                        )
                        text = "\n".join(lines)
                        chain = MessageEventResult().message(text)
                        if await self._send_chain(session, chain):
                            post_id = post.get("id")
                            if post_id is not None:
                                sent_ids.append(int(post_id))
                    if sent_ids:
                        await self.services.subscriptions.mark_sent_post_ids(
                            group_id,
                            sent_ids,
                            round_id,
                            dedupe_rounds,
                        )
                    if max_id:
                        await self.services.subscriptions.update_last_post(group_id, tag, int(max_id))

    async def _dispatch_popular_subscriptions(self, round_id: int) -> None:
        if not self.services or not self.command_ctx or not self.config:
            return
        groups = await self.services.subscriptions.list_groups()
        limit = min(self._get_search_limit(), 20)
        only_image = bool(self.config.display.only_image)
        show_preview = bool(self.config.display.show_preview)
        dedupe_rounds = max(int(self.config.subscriptions.dedupe_rounds), 0)
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

                selected_ids = [post.get("id") for post, _ in selected]
                for group_id, session in entries:
                    new_ids = await self.services.subscriptions.filter_new_post_ids(
                        group_id,
                        selected_ids,
                        round_id,
                        dedupe_rounds,
                    )
                    group_selected = [
                        item
                        for item in selected
                        if item[0].get("id") in new_ids
                    ]
                    if not group_selected:
                        await self.services.subscriptions.update_popular_sent(group_id, now_ts)
                        continue

                    sent_ids: list[int] = []
                    if only_image:
                        chain = _build_image_chain([url for _, url in group_selected])
                        if chain and await self._send_chain(session, chain):
                            sent_ids.extend(
                                [
                                    int(post.get("id"))
                                    for post, _ in group_selected
                                    if post.get("id") is not None
                                ]
                            )
                    else:
                        total = len(group_selected)
                        for idx, (post, url) in enumerate(group_selected, 1):
                            score = post.get("score", 0)
                            fav = post.get("fav_count", 0)
                            rating = post.get("rating", "?")
                            tags_text = _format_tags(
                                self.command_ctx,
                                post.get("tag_string", ""),
                            )
                            lines = [
                                f"🔥 热门订阅 ({scale}，第{idx}/{total}条)",
                                f"#{post['id']} | ⭐{score} ❤️{fav} | {rating}",
                            ]
                            if tags_text:
                                lines.append(f"🏷️ 标签: {tags_text}")
                            lines.append(
                                f"🔗 https://danbooru.donmai.us/posts/{post['id']}"
                            )
                            text = "\n".join(lines)
                            chain = _build_text_image_chain(text, url)
                            if chain and await self._send_chain(session, chain):
                                post_id = post.get("id")
                                if post_id is not None:
                                    sent_ids.append(int(post_id))
                    if sent_ids:
                        await self.services.subscriptions.mark_sent_post_ids(
                            group_id,
                            sent_ids,
                            round_id,
                            dedupe_rounds,
                        )
                    await self.services.subscriptions.update_popular_sent(group_id, now_ts)
            else:
                for group_id, session in entries:
                    post_ids = [post.get("id") for post in posts[:limit]]
                    new_ids = await self.services.subscriptions.filter_new_post_ids(
                        group_id,
                        post_ids,
                        round_id,
                        dedupe_rounds,
                    )
                    filtered_posts = [
                        post for post in posts[:limit] if post.get("id") in new_ids
                    ]
                    if not filtered_posts:
                        await self.services.subscriptions.update_popular_sent(group_id, now_ts)
                        continue

                    result_lines = [f"🔥 热门订阅 ({scale})\n"]
                    for idx, post in enumerate(filtered_posts, 1):
                        score = post.get("score", 0)
                        fav = post.get("fav_count", 0)
                        result_lines.append(f"{idx}. #{post['id']} | ⭐{score} ❤️{fav}")

                    text = "\n".join(result_lines)
                    chain = MessageEventResult().message(text)
                    if await self._send_chain(session, chain):
                        sent_ids = [
                            int(post.get("id"))
                            for post in filtered_posts
                            if post.get("id") is not None
                        ]
                        if sent_ids:
                            await self.services.subscriptions.mark_sent_post_ids(
                                group_id,
                                sent_ids,
                                round_id,
                                dedupe_rounds,
                            )
                    await self.services.subscriptions.update_popular_sent(group_id, now_ts)

    async def _run_subscription_cycle(self) -> None:
        while True:
            if self._subscription_stop and self._subscription_stop.is_set():
                break
            try:
                round_id = 0
                if self.services:
                    round_id = await self.services.subscriptions.next_dedupe_round()
                await self._dispatch_tag_subscriptions(round_id)
                await self._dispatch_popular_subscriptions(round_id)
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
                    yield result
            except Exception as e:
                async for result in self._handle_error(event, e):
                    yield result
        else:
            tag_query = " ".join(part for part in [sub_cmd, args] if part).strip()
            posts_handler = self.handlers.get("posts") if self.handlers else None
            if posts_handler and tag_query:
                try:
                    async for result in posts_handler(event, tag_query):
                        yield result
                    return
                except Exception as e:
                    async for result in self._handle_error(event, e):
                        yield result
                    return

            yield event.plain_result(
                f"❌ 未知命令: {sub_cmd}\n\n使用 `/danbooru help` 查看帮助"
            )
