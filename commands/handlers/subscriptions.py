"""Subscription command handlers."""

from typing import Dict, AsyncIterator, Optional

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler
import time

from .posts import (
    _apply_filters,
    _build_image_chain,
    _build_text_image_chain,
    _is_image_accessible,
    _select_image_url,
)


MESSAGES = {
    "group_only": "❌ 订阅功能仅支持群聊使用",
    "missing_tag": "❌ 请提供订阅标签\n用法: `/danbooru subscribe <tag>`",
    "missing_unsub": "❌ 请提供取消订阅的标签\n用法: `/danbooru unsubscribe <tag>`",
    "subscribe_disabled": "❌ 当前配置已禁用订阅功能",
    "subscribe_popular_ok": "✅ 已订阅热门",
    "unsubscribe_popular_ok": "✅ 已取消热门订阅",
    "subscribe_tag_ok": "✅ 已订阅标签: {tag}",
    "unsubscribe_tag_ok": "✅ 已取消订阅标签: {tag}",
    "unsubscribe_tag_missing": "⚠️ 该标签未订阅: {tag}",
    "invalid_scale": "❌ scale 参数仅支持 day/week/month",
    "no_subscriptions": "ℹ️ 当前群聊暂无订阅",
}


def _group_session(event: AstrMessageEvent) -> Optional[str]:
    if not event.get_group_id():
        return None
    return getattr(event, "unified_msg_origin", None) or str(getattr(event, "session", ""))


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_subscribe(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not ctx.config or not ctx.config.subscriptions.enabled:
            yield event.plain_result(MESSAGES["subscribe_disabled"])
            return

        session = _group_session(event)
        if not session:
            yield event.plain_result(MESSAGES["group_only"])
            return

        parsed = ctx.parser.parse_args(args)
        if not parsed.positional:
            yield event.plain_result(MESSAGES["missing_tag"])
            return

        raw = " ".join(parsed.positional).strip()
        primary = parsed.positional[0].lower()
        group_id = event.get_group_id()

        if primary in {"popular", "hot"}:
            scale = parsed.flags.get("scale", "day")
            if scale not in {"day", "week", "month"}:
                yield event.plain_result(MESSAGES["invalid_scale"])
                return
            await ctx.services.subscriptions.set_popular(
                group_id,
                enabled=True,
                platform=event.get_platform_id(),
                session_id=session,
                scale=scale,
            )
            response = await ctx.services.explore.popular(scale=scale)
            if response.success and response.data:
                posts = response.data
                default_limit = 5
                if ctx.config:
                    limit = ctx.config.resolve_batch_limit(None, default_limit, 20)
                    show_preview = ctx.config.display.show_preview
                    only_image = ctx.config.display.only_image
                    dedupe_rounds = max(int(ctx.config.subscriptions.dedupe_rounds), 0)
                else:
                    limit = default_limit
                    show_preview = True
                    only_image = False
                    dedupe_rounds = 0
                current_round = await ctx.services.subscriptions.get_dedupe_round()

                if show_preview or only_image:
                    selected: list[tuple[dict, str]] = []
                    for post in posts:
                        url = _select_image_url(ctx, post)
                        if not url:
                            continue
                        if not await _is_image_accessible(ctx, url):
                            continue
                        selected.append((post, url))
                        if len(selected) >= limit:
                            break

                    if selected:
                        post_ids = [post.get("id") for post, _ in selected]
                        new_ids = await ctx.services.subscriptions.filter_new_post_ids(
                            group_id,
                            post_ids,
                            current_round,
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
                            if chain:
                                yield chain
                        else:
                            total = len(selected)
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
                                    yield chain
                    else:
                        yield event.plain_result(MESSAGES["subscribe_popular_ok"])
                else:
                    post_ids = [post.get("id") for post in posts[:limit]]
                    new_ids = await ctx.services.subscriptions.filter_new_post_ids(
                        group_id,
                        post_ids,
                        current_round,
                        dedupe_rounds,
                    )
                    filtered_posts = [
                        post for post in posts[:limit] if post.get("id") in new_ids
                    ]
                    if not filtered_posts:
                        yield event.plain_result(MESSAGES["subscribe_popular_ok"])
                    else:
                        result_lines = [f"🔥 热门订阅 ({scale})\n"]
                        for idx, post in enumerate(filtered_posts, 1):
                            score = post.get("score", 0)
                            fav = post.get("fav_count", 0)
                            result_lines.append(f"{idx}. #{post['id']} | ⭐{score} ❤️{fav}")
                        yield event.plain_result("\n".join(result_lines))
            else:
                yield event.plain_result(MESSAGES["subscribe_popular_ok"])

            await ctx.services.subscriptions.update_popular_sent(group_id, int(time.time()))
            return

        tag = raw
        await ctx.services.subscriptions.subscribe_tag(
            group_id,
            tag,
            platform=event.get_platform_id(),
            session_id=session,
        )

        # 初始化 last_post_id，避免订阅后立刻推送旧内容
        query = _apply_filters(ctx, tag)
        if query:
            query = f"{query} order:id_desc"
        else:
            query = f"{tag} order:id_desc"
        response = await ctx.services.posts.list(tags=query, limit=1)
        if response.success and response.data:
            latest_id = response.data[0].get("id")
            if latest_id:
                await ctx.services.subscriptions.update_last_post(group_id, tag, int(latest_id))

        yield event.plain_result(MESSAGES["subscribe_tag_ok"].format(tag=tag))

    async def cmd_unsubscribe(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not ctx.config or not ctx.config.subscriptions.enabled:
            yield event.plain_result(MESSAGES["subscribe_disabled"])
            return

        session = _group_session(event)
        if not session:
            yield event.plain_result(MESSAGES["group_only"])
            return

        if not args:
            yield event.plain_result(MESSAGES["missing_unsub"])
            return

        parsed = ctx.parser.parse_args(args)
        if not parsed.positional:
            yield event.plain_result(MESSAGES["missing_unsub"])
            return

        raw = " ".join(parsed.positional).strip()
        primary = parsed.positional[0].lower()
        group_id = event.get_group_id()

        if primary in {"popular", "hot"}:
            await ctx.services.subscriptions.set_popular(
                group_id,
                enabled=False,
                platform=event.get_platform_id(),
                session_id=session,
            )
            yield event.plain_result(MESSAGES["unsubscribe_popular_ok"])
            return

        ok = await ctx.services.subscriptions.unsubscribe_tag(group_id, raw)
        if not ok:
            yield event.plain_result(MESSAGES["unsubscribe_tag_missing"].format(tag=raw))
            return
        yield event.plain_result(MESSAGES["unsubscribe_tag_ok"].format(tag=raw))

    async def cmd_subscriptions(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        session = _group_session(event)
        if not session:
            yield event.plain_result(MESSAGES["group_only"])
            return

        group_id = event.get_group_id()
        group = await ctx.services.subscriptions.list_group(group_id)
        if not group:
            yield event.plain_result(MESSAGES["no_subscriptions"])
            return

        tags = sorted(group.get("tags", {}).keys())
        popular_cfg = group.get("popular", {})
        popular_enabled = bool(popular_cfg.get("enabled"))
        popular_scale = popular_cfg.get("scale", "day")

        lines = ["📌 当前群聊订阅"]
        lines.append(
            f"🔥 热门订阅: {'开启' if popular_enabled else '关闭'}"
            f"{f' ({popular_scale})' if popular_enabled else ''}"
        )
        if tags:
            lines.append("\n🏷️ 标签订阅:")
            for tag in tags:
                lines.append(f"- {tag}")
        else:
            lines.append("\n🏷️ 标签订阅: (无)")

        yield event.plain_result("\n".join(lines))

    return {
        "subscribe": cmd_subscribe,
        "unsubscribe": cmd_unsubscribe,
        "subscriptions": cmd_subscriptions,
    }
