"""
Tag command handlers.
"""

from typing import Dict, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


MESSAGES = {
    "missing_tag": "❌ 请提供标签名\n用法: `/danbooru tag <name>`",
    "tag_not_found": "❌ 未找到标签: {name}",
    "missing_query": "❌ 请提供搜索词\n用法: `/danbooru tags <query>`",
    "search_failed": "❌ 搜索失败",
    "tag_search_empty": "⚠️ 未找到匹配的标签: {query}",
    "missing_related": "❌ 请提供标签\n用法: `/danbooru related <tag>`",
    "related_failed": "❌ 获取相关标签失败",
    "related_empty": "⚠️ 未找到相关标签: {tag}",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_tag(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_tag"])
            return

        tag_name = args.strip()
        response = await ctx.services.tags.list(name_matches=tag_name, limit=1)
        if not response.success or not response.data:
            yield event.plain_result(MESSAGES["tag_not_found"].format(name=tag_name))
            return

        tag = response.data[0]
        category_names = {0: "general", 1: "artist", 3: "copyright", 4: "character", 5: "meta"}
        cat_name = category_names.get(tag.get('category', 0), "unknown")

        info = f"""🏷️ 标签: {tag['name']}

📁 类别: {cat_name}
📊 帖子数: {tag.get('post_count', 0)}
🆔 ID: {tag['id']}

🔗 链接: https://danbooru.donmai.us/posts?tags={tag['name']}
"""
        yield event.plain_result(info)

    async def cmd_tags(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        parsed = ctx.parser.parse_args(args)
        if not parsed.positional:
            yield event.plain_result(MESSAGES["missing_query"])
            return

        query = parsed.positional[0]
        category = parsed.flags.get("category")
        limit = min(int(parsed.flags.get("limit", 10)), 50)

        cat_int = int(category) if category else None
        response = await ctx.services.tags.list(name_matches=query, category=cat_int, limit=limit)

        if not response.success:
            yield event.plain_result(MESSAGES["search_failed"])
            return

        tags = response.data
        if not tags:
            yield event.plain_result(MESSAGES["tag_search_empty"].format(query=query))
            return

        category_names = {0: "G", 1: "A", 3: "©", 4: "C", 5: "M"}
        result_lines = [f"🏷️ 标签搜索: {query} (共{len(tags)}个)\n"]
        for tag in tags:
            cat = category_names.get(tag.get('category', 0), "?")
            result_lines.append(f"[{cat}] {tag['name']} ({tag.get('post_count', 0)})")

        yield event.plain_result("\n".join(result_lines))

    async def cmd_related(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_related"])
            return

        response = await ctx.services.related_tags.get(args.strip())
        if not response.success:
            yield event.plain_result(MESSAGES["related_failed"])
            return

        data = response.data
        if not data:
            yield event.plain_result(MESSAGES["related_empty"].format(tag=args))
            return

        result_lines = [f"🔗 相关标签: {args}\n"]
        related = data.get('related_tags', [])[:15]
        for item in related:
            if isinstance(item, dict):
                result_lines.append(f"- {item.get('tag', {}).get('name', 'unknown')}")
            elif isinstance(item, list) and len(item) >= 2:
                result_lines.append(f"- {item[0]}")

        yield event.plain_result("\n".join(result_lines))

    return {
        "tag": cmd_tag,
        "tags": cmd_tags,
        "related": cmd_related,
    }
