"""
Wiki command handlers.
"""

from typing import Dict, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


MESSAGES = {
    "missing_title": "❌ 请提供Wiki标题\n用法: `/danbooru wiki <title>`",
    "wiki_not_found": "❌ 未找到Wiki页面: {title}",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_wiki(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_title"])
            return

        title = args.strip()
        response = await ctx.services.wiki.get_by_title(title)
        if not response.success or not response.data:
            yield event.plain_result(MESSAGES["wiki_not_found"].format(title=title))
            return

        wiki_page = response.data
        body = wiki_page.get('body', '')[:500]
        if len(wiki_page.get('body', '')) > 500:
            body += "..."

        info = f"""📝 Wiki: {wiki_page.get('title', title)}

🆔 ID: {wiki_page.get('id', 'unknown')}
📅 更新: {wiki_page.get('updated_at', 'unknown')[:10] if wiki_page.get('updated_at') else 'unknown'}

📄 内容:
{body}

🔗 链接: https://danbooru.donmai.us/wiki_pages/{title}
"""
        yield event.plain_result(info)

    return {"wiki": cmd_wiki}
