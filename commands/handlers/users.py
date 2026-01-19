"""
User command handlers.
"""

from typing import Dict, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


MESSAGES = {
    "missing_user": "❌ 请提供用户ID或用户名\n用法: `/danbooru user <id/name>`",
    "user_not_found": "❌ 未找到用户: {user}",
    "missing_user_id": "❌ 请提供用户ID\n用法: `/danbooru favorites <user_id>`",
    "favorites_failed": "❌ 获取收藏失败",
    "favorites_empty": "⚠️ 该用户没有收藏",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_user(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_user"])
            return

        raw = args.strip()
        try:
            user_id = int(raw)
            response = await ctx.services.users.get(user_id)
        except ValueError:
            response = await ctx.services.users.list(name_matches=raw, limit=1)
            if response.success and response.data:
                response.data = response.data[0]
            else:
                yield event.plain_result(MESSAGES["user_not_found"].format(user=raw))
                return

        if not response.success or not response.data:
            yield event.plain_result(MESSAGES["user_not_found"].format(user=raw))
            return

        user = response.data
        info = f"""👤 用户: {user['name']}

🆔 ID: {user['id']}
🎖️ 等级: {user.get('level_string', 'unknown')}
📅 注册: {user.get('created_at', 'unknown')[:10] if user.get('created_at') else 'unknown'}

⬆️ 上传: {user.get('post_upload_count', 0)}
✏️ 编辑: {user.get('post_update_count', 0)}
💬 评论: {user.get('comment_count', 0)}
📝 笔记: {user.get('note_update_count', 0)}

🔗 链接: https://danbooru.donmai.us/users/{user['id']}
"""
        yield event.plain_result(info)

    async def cmd_favorites(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        parsed = ctx.parser.parse_args(args)
        user_id = int(parsed.positional[0]) if parsed.positional else None
        limit = min(int(parsed.flags.get("limit", 10)), 30)

        if not user_id:
            yield event.plain_result(MESSAGES["missing_user_id"])
            return

        response = await ctx.services.favorites.list(user_id=user_id, limit=limit)
        if not response.success:
            yield event.plain_result(MESSAGES["favorites_failed"])
            return

        favs = response.data
        if not favs:
            yield event.plain_result(MESSAGES["favorites_empty"])
            return

        result_lines = [f"❤️ 用户收藏 (共{len(favs)}个)\n"]
        for fav in favs:
            post_id = fav.get('post_id', fav.get('id', 0))
            result_lines.append(f"- 帖子 #{post_id}")

        yield event.plain_result("\n".join(result_lines))

    return {
        "user": cmd_user,
        "favorites": cmd_favorites,
    }
