"""
Artist command handlers.
"""

from typing import Dict, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


MESSAGES = {
    "missing_artist": "❌ 请提供艺术家名\n用法: `/danbooru artist <name>`",
    "artist_not_found": "❌ 未找到艺术家: {name}",
    "missing_query": "❌ 请提供搜索词\n用法: `/danbooru artists <query>`",
    "search_failed": "❌ 搜索失败",
    "artist_search_empty": "⚠️ 未找到艺术家: {query}",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_artist(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_artist"])
            return

        response = await ctx.services.artists.list(name_matches=args.strip(), limit=1)
        if not response.success or not response.data:
            yield event.plain_result(MESSAGES["artist_not_found"].format(name=args))
            return

        artist = response.data[0]
        urls = artist.get('urls') or []
        if not urls:
            url_response = await ctx.services.artists.get_urls(artist_id=artist["id"])
            if url_response.success and url_response.data:
                urls = url_response.data
        url_str = "\n".join([f"  - {u.get('url', '')}" for u in urls[:5]]) if urls else "无"

        info = f"""🎨 艺术家: {artist['name']}

🆔 ID: {artist['id']}
🏷️ 其他名称: {', '.join(artist.get('other_names', [])) or '无'}
🔗 链接:
{url_str}

🔗 Danbooru: https://danbooru.donmai.us/artists/{artist['id']}
"""
        yield event.plain_result(info)

    async def cmd_artists(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        parsed = ctx.parser.parse_args(args)
        if not parsed.positional:
            yield event.plain_result(MESSAGES["missing_query"])
            return

        query = parsed.positional[0]
        limit = min(int(parsed.flags.get("limit", 10)), 30)

        response = await ctx.services.artists.list(name_matches=f"*{query}*", limit=limit)
        if not response.success:
            yield event.plain_result(MESSAGES["search_failed"])
            return

        artists = response.data
        if not artists:
            yield event.plain_result(MESSAGES["artist_search_empty"].format(query=query))
            return

        result_lines = [f"🎨 艺术家搜索: {query} (共{len(artists)}个)\n"]
        for artist in artists:
            banned = "🚫" if artist.get('is_banned') else ""
            result_lines.append(f"- {artist['name']} {banned}")

        yield event.plain_result("\n".join(result_lines))

    return {
        "artist": cmd_artist,
        "artists": cmd_artists,
    }
