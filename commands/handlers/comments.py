"""
Comment command handlers.
"""

from typing import Dict, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


MESSAGES = {
    "missing_post_id": "❌ 请提供帖子ID\n用法: `/danbooru comments <post_id>`",
    "invalid_post_id": "❌ 无效的帖子ID",
    "comments_failed": "❌ 获取评论失败",
    "comments_empty": "⚠️ 帖子 #{post_id} 没有评论",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_comments(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_post_id"])
            return

        try:
            post_id = int(args.strip())
        except ValueError:
            yield event.plain_result(MESSAGES["invalid_post_id"])
            return

        default_limit = 10
        if ctx.config:
            limit = ctx.config.resolve_batch_limit(None, default_limit, 50)
        else:
            limit = default_limit
        response = await ctx.services.comments.list(post_id=post_id, limit=limit)
        if not response.success:
            yield event.plain_result(MESSAGES["comments_failed"])
            return

        comments = response.data
        if not comments:
            yield event.plain_result(MESSAGES["comments_empty"].format(post_id=post_id))
            return

        result_lines = [f"💬 帖子 #{post_id} 的评论 (共{len(comments)}条)\n"]
        for comment in comments:
            creator = comment.get('creator_name', 'unknown')
            body = comment.get('body', '')[:100]
            if len(comment.get('body', '')) > 100:
                body += "..."
            result_lines.append(f"{creator}: {body}\n")

        yield event.plain_result("\n".join(result_lines))

    return {"comments": cmd_comments}
