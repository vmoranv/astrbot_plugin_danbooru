"""
Help command handlers.
"""

from typing import Dict, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


HELP_MESSAGES = {
    "main": """🔎 Danbooru API 插件帮助

这是一个完整的 Danbooru API 封装插件，支持以下功能：

📝 帖子管理
`/danbooru post <id>` - 获取帖子详情
`/danbooru posts [tags]` - 搜索帖子
`/danbooru <tag>` - 主命令直接按标签搜索
`/danbooru random [tags]` - 随机帖子
`/danbooru popular [date]` - 热门帖子

🏷️ 标签管理
`/danbooru tag <name>` - 获取标签信息
`/danbooru tags <query>` - 搜索标签
`/danbooru related <tag>` - 相关标签

👤 用户相关
`/danbooru user <id/name>` - 用户信息
`/danbooru favorites [user]` - 收藏列表

🎨 艺术家
`/danbooru artist <name>` - 艺术家信息
`/danbooru artists <query>` - 搜索艺术家

🧺 池/集合
`/danbooru pool <id>` - 池详情
`/danbooru pools [query]` - 搜索池

📝 Wiki
`/danbooru wiki <title>` - Wiki页面

💬 评论
`/danbooru comments <post_id>` - 帖子评论

🔍 其他
`/danbooru autocomplete <query>` - 自动补全
`/danbooru count <tags>` - 帖子计数
`/danbooru status` - 系统状态
`/danbooru api <method> <endpoint> ...` - 原始API调用（全量覆盖）
`/danbooru call <service> <method> ...` - 调用服务方法（微服务入口）

📌 订阅（群聊）
`/danbooru subscribe <tag>` - 订阅标签更新
`/danbooru subscribe popular [--scale day|week|month]` - 订阅热门
`/danbooru unsubscribe <tag>` - 取消订阅
`/danbooru subscriptions` - 查看订阅

📖 使用 `/danbooru help <命令>` 获取详细帮助
""",
    "post": """📸 帖子命令帮助

`/danbooru post <id>` - 获取指定ID的帖子详情

示例:
`/danbooru post 12345` - 获取帖子 #12345
""",
    "posts": """🔍 搜索帖子帮助

`/danbooru posts [tags] [--page N] [--limit N]`

参数:
- `tags`: 搜索标签（空格分隔）
- `--page N`: 页码（默认1）
- `--limit N`: 每页数量（默认 display.search_limit，最大20）
- 如果只传数字，会按 `id` 搜索

示例:
`/danbooru posts 1girl solo` - 搜索标签
`/danbooru posts touhou --limit 10` - 限制结果数量
""",
    "random": """🎲 随机帖子帮助

`/danbooru random [tags]`

参数:
- `tags`: 可选的过滤标签

示例:
`/danbooru random` - 完全随机
`/danbooru random landscape` - 随机风景图
""",
    "tag": """🏷️ 标签信息帮助

`/danbooru tag <name>` - 获取标签详细信息

示例:
`/danbooru tag touhou` - 获取东方标签信息
""",
    "tags": """🏷️ 搜索标签帮助

`/danbooru tags <query> [--category N] [--limit N]`

参数:
- `query`: 搜索词（支持通配符*）
- `--category N`: 类别过滤（0=general, 1=artist, 3=copyright, 4=character, 5=meta）
- `--limit N`: 结果数量

示例:
`/danbooru tags touhou*` - 搜索以touhou开头的标签
`/danbooru tags *girl --category 4` - 搜索角色标签
""",
    "artist": """🎨 艺术家信息帮助

`/danbooru artist <name>` - 获取艺术家信息

示例:
`/danbooru artist ke-ta` - 获取艺术家ke-ta的信息
""",
    "pool": """🧺 池帮助

`/danbooru pool <id>` - 获取池详情
`/danbooru pools [query]` - 搜索池

示例:
`/danbooru pool 12345` - 获取池 #12345
`/danbooru pools touhou` - 搜索包含touhou的池
""",
    "user": """👤 用户帮助

`/danbooru user <id/name>` - 获取用户信息

示例:
`/danbooru user 12345` - 按ID获取
`/danbooru user username` - 按用户名获取
""",
    "wiki": """📝 Wiki帮助

`/danbooru wiki <title>` - 获取Wiki页面

示例:
`/danbooru wiki touhou` - 获取东方Wiki页面
""",
    "subscribe": """📌 订阅帮助

`/danbooru subscribe <tag>` - 订阅指定标签的新帖推送
`/danbooru subscribe popular [--scale day|week|month]` - 订阅热门推送

说明:
- 仅群聊可用
- scale 默认 day
- 订阅后只推送新内容
""",
    "unsubscribe": """📌 取消订阅帮助

`/danbooru unsubscribe <tag>` - 取消指定标签订阅
`/danbooru unsubscribe popular` - 取消热门订阅
""",
    "subscriptions": """📌 订阅列表帮助

`/danbooru subscriptions` - 查看当前群聊订阅
""",
    "api": """🧰 原始API调用帮助

`/danbooru api <METHOD> <endpoint> [key=value ...] [--json '{...}'] [--auth header|params|none] [--format json|xml] [--no-cache]`

说明:
- METHOD 支持 GET/POST/PUT/PATCH/DELETE，不填默认 GET
- endpoint 可用 `posts/123` 或完整路径，自动补 `.json`
- `key=value` 会根据方法自动放入 query 或 body
- `--json` 传入 JSON 字符串（需用引号包裹）
- `--auth none` 可关闭认证；`--format xml` 获取 XML

示例:
`/danbooru api posts?tags=1girl`  （默认 GET）
`/danbooru api GET posts limit=5`
`/danbooru api PUT posts/6 --json '{"post":{"rating":"s"}}'`
`/danbooru api GET tags --auth params --format json`
""",
    "call": """🧩 服务方法调用帮助

`/danbooru call <service> <method> [key=value ...] [--json '{...}'] [--args '[...]']`
`/danbooru call services` - 列出可用服务
`/danbooru call methods <service>` - 列出服务可用方法

说明:
- `key=value` 作为关键字参数传入
- `--args` 可传入 JSON 数组作为位置参数
- `--json` 传入 JSON 对象合并为关键字参数

示例:
`/danbooru call posts list tags=1girl limit=5`
`/danbooru call wiki get_by_title title=touhou`
`/danbooru call moderation list_post_flags post_id=123`
""",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_help(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        topic = args.strip().lower() if args else "main"
        if topic in ctx.help_messages:
            yield event.plain_result(ctx.help_messages[topic])
            return
        topics = ", ".join(ctx.help_messages.keys())
        yield event.plain_result(
            f"❌ 未知帮助主题: {topic}\n\n可用主题: {topics}\n"
        )

    return {"help": cmd_help}
