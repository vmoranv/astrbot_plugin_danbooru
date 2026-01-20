"""
Misc command handlers.
"""

from typing import Dict, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


MESSAGES = {
    "missing_query": "❌ 请提供搜索词\n用法: `/danbooru autocomplete <query>`",
    "autocomplete_failed": "❌ 自动补全失败",
    "autocomplete_empty": "⚠️ 未找到匹配: {query}",
    "count_failed": "❌ 获取计数失败",
    "status_failed": "❌ 获取状态失败",
    "missing_post_id": "❌ 请提供帖子ID\n用法: `/danbooru similar <post_id>`",
    "invalid_post_id": "❌ 无效的帖子ID",
    "similar_failed": "❌ 搜索相似图片失败",
    "similar_empty": "⚠️ 未找到与帖子 #{post_id} 相似的图片",
}


def _format_bytes(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_autocomplete(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_query"])
            return

        default_limit = 10
        if ctx.config:
            limit = ctx.config.resolve_batch_limit(None, default_limit, 50)
        else:
            limit = default_limit
        response = await ctx.services.autocomplete.tag(args.strip(), limit=limit)
        if not response.success:
            yield event.plain_result(MESSAGES["autocomplete_failed"])
            return

        results = response.data
        if not results:
            yield event.plain_result(MESSAGES["autocomplete_empty"].format(query=args))
            return

        result_lines = [f"🔍 自动补全: {args}\n"]
        for item in results:
            if isinstance(item, dict):
                name = item.get('value') or item.get('name', 'unknown')
                result_lines.append(f"- {name}")
            else:
                result_lines.append(f"- {item}")

        yield event.plain_result("\n".join(result_lines))

    async def cmd_count(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        tags = args.strip() if args else None
        response = await ctx.services.counts.posts(tags=tags)
        if not response.success:
            yield event.plain_result(MESSAGES["count_failed"])
            return

        data = response.data
        count = data.get('counts', {}).get('posts', 0) if isinstance(data, dict) else 0
        if tags:
            yield event.plain_result(f"📊 标签 `{tags}` 的帖子数: {count:,}")
        else:
            yield event.plain_result(f"📊 总帖子数: {count:,}")

    async def cmd_status(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        response = await ctx.services.status.get()
        if not response.success:
            yield event.plain_result(MESSAGES["status_failed"])
            return

        stats = ctx.client.get_stats()
        info = f"""📈 Danbooru 插件状态

🌐 API: {ctx.config.api.active_url if ctx.config else 'unknown'}
🔐 已认证: {'是' if stats.get('is_authenticated') else '否'}
📡 请求次数: {stats.get('request_count', 0)}

✅ 服务正常运行
"""
        yield event.plain_result(info)

    async def cmd_clear_cache(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        stats = await ctx.client.clear_cache_with_stats()
        count = stats.get("count", 0)
        size_bytes = stats.get("size_bytes", 0)
        size_text = _format_bytes(int(size_bytes))
        yield event.plain_result(
            f"🧹 已清理缓存: {count} 条，约 {size_text}（不含订阅与去重数据）"
        )

    async def cmd_similar(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_post_id"])
            return

        try:
            post_id = int(args.strip())
        except ValueError:
            yield event.plain_result(MESSAGES["invalid_post_id"])
            return

        response = await ctx.services.iqdb.search_by_post(post_id)
        if not response.success:
            yield event.plain_result(MESSAGES["similar_failed"])
            return

        results = response.data
        if not results:
            yield event.plain_result(MESSAGES["similar_empty"].format(post_id=post_id))
            return

        default_limit = 10
        if ctx.config:
            limit = ctx.config.resolve_batch_limit(None, default_limit, 50)
        else:
            limit = default_limit
        result_lines = [f"🔎 与帖子 #{post_id} 相似的图片\n"]
        for item in results[:limit]:
            if isinstance(item, dict):
                similar_id = item.get('post_id') or item.get('id', 0)
                score = item.get('score', 0)
                result_lines.append(f"- 帖子 #{similar_id} (相似度: {score}%)")

        yield event.plain_result("\n".join(result_lines))

    return {
        "autocomplete": cmd_autocomplete,
        "count": cmd_count,
        "status": cmd_status,
        "clearcache": cmd_clear_cache,
        "similar": cmd_similar,
    }
