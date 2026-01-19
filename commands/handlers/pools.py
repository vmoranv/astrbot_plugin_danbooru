"""
Pool command handlers.
"""

from typing import Dict, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


MESSAGES = {
    "missing_pool_id": "❌ 请提供池ID\n用法: `/danbooru pool <id>`",
    "invalid_pool_id": "❌ 无效的池ID",
    "pool_fetch_failed": "❌ 获取池失败",
    "pool_search_failed": "❌ 搜索失败",
    "pool_search_empty": "⚠️ 未找到池: {query}",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_pool(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_pool_id"])
            return

        try:
            pool_id = int(args.strip())
        except ValueError:
            yield event.plain_result(MESSAGES["invalid_pool_id"])
            return

        response = await ctx.services.pools.get(pool_id)
        if not response.success:
            yield event.plain_result(MESSAGES["pool_fetch_failed"])
            return

        pool = response.data
        post_ids = pool.get('post_ids', [])
        info = f"""🧺 池 #{pool['id']}

📝 名称: {pool['name']}
📁 类别: {pool.get('category', 'unknown')}
📊 帖子数: {len(post_ids)}
📄 描述: {pool.get('description', '无')[:200]}

🔗 链接: https://danbooru.donmai.us/pools/{pool['id']}
"""
        yield event.plain_result(info)

    async def cmd_pools(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        parsed = ctx.parser.parse_args(args)
        query = " ".join(parsed.positional) if parsed.positional else None
        default_limit = 10
        requested = int(parsed.flags.get("limit", default_limit))
        if ctx.config:
            limit = ctx.config.resolve_batch_limit(requested, default_limit, 30)
        else:
            limit = min(requested, 30)

        response = await ctx.services.pools.list(name_matches=f"*{query}*" if query else None, limit=limit)
        if not response.success:
            yield event.plain_result(MESSAGES["pool_search_failed"])
            return

        pools = response.data
        if not pools:
            yield event.plain_result(MESSAGES["pool_search_empty"].format(query=query))
            return

        result_lines = [f"🧺 池搜索 (共{len(pools)}个)\n"]
        for pool in pools:
            post_count = len(pool.get('post_ids', []))
            result_lines.append(f"#{pool['id']} | {pool['name']} ({post_count}帖)")

        yield event.plain_result("\n".join(result_lines))

    return {
        "pool": cmd_pool,
        "pools": cmd_pools,
    }
