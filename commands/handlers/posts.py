"""
Post command handlers.
"""

from typing import Dict, AsyncIterator, Iterable, List, Optional

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler


MESSAGES = {
    "missing_post_id": "❌ 请提供帖子ID\n用法: `/danbooru post <id>`",
    "invalid_post_id": "❌ 无效的帖子ID",
    "post_fetch_failed": "❌ 获取帖子失败",
    "posts_search_failed": "❌ 搜索失败",
    "posts_not_found": "⚠️ 未找到匹配的帖子",
    "random_failed": "❌ 获取随机帖子失败",
    "popular_failed": "❌ 获取热门帖子失败",
    "popular_empty": "⚠️ 暂无热门帖子",
}

VALID_RATINGS = ("g", "s", "q", "e")


def _select_image_url(ctx: CommandContext, post: dict) -> Optional[str]:
    size = ctx.config.display.preview_size if ctx.config else "preview"
    if size == "original":
        return post.get("file_url") or post.get("large_file_url") or post.get("preview_file_url")
    if size == "sample":
        return post.get("large_file_url") or post.get("file_url") or post.get("preview_file_url")
    return post.get("preview_file_url") or post.get("large_file_url") or post.get("file_url")


def _build_image_chain(urls: Iterable[str]) -> Optional[MessageEventResult]:
    result = MessageEventResult()
    has_item = False
    for url in urls:
        if not url:
            continue
        result.url_image(url)
        has_item = True
    return result if has_item else None


def _build_text_image_chain(text: str, url: Optional[str]) -> Optional[MessageEventResult]:
    if not url:
        return None
    result = MessageEventResult()
    result.url_image(url)
    result.message(text)
    return result


def _apply_filters(ctx: CommandContext, tags: Optional[str]) -> Optional[str]:
    if not ctx.config:
        return tags

    tokens: List[str] = tags.split() if tags else []
    if not tokens:
        tokens = []

    has_rating = any(token.startswith("rating:") or token.startswith("-rating:") for token in tokens)

    if ctx.config.filter.required_tags:
        tokens.extend([tag for tag in ctx.config.filter.required_tags if tag])

    if ctx.config.filter.blocked_tags:
        tokens.extend([f"-{tag}" for tag in ctx.config.filter.blocked_tags if tag])

    if not has_rating:
        allowed = [rating for rating in ctx.config.filter.allowed_ratings if rating in VALID_RATINGS]
        if not allowed:
            allowed = ["g", "s"]
        disallowed = [rating for rating in VALID_RATINGS if rating not in allowed]
        tokens.extend([f"-rating:{rating}" for rating in disallowed])

    min_score = ctx.config.filter.min_score
    if min_score is not None and min_score > 0:
        tokens.append(f"score:>={min_score}")

    return " ".join(tokens) if tokens else None


def _apply_limit(ctx: CommandContext, limit: int) -> int:
    if ctx.config:
        max_results = ctx.config.filter.max_results
        if max_results:
            return min(limit, max_results)
    return limit


def _only_image(ctx: CommandContext) -> bool:
    return bool(ctx.config and ctx.config.display.only_image)



def _show_preview(ctx: CommandContext) -> bool:
    return bool(ctx.config and ctx.config.display.show_preview)


def _format_tags(ctx: CommandContext, tag_string: str) -> str:
    if not tag_string:
        return ""
    if ctx.config and not ctx.config.display.show_tags:
        return ""
    tags = tag_string.split()
    per_line = 12
    if ctx.config and ctx.config.display.max_tags_display > 0:
        per_line = ctx.config.display.max_tags_display
    lines = [" ".join(tags[i:i + per_line]) for i in range(0, len(tags), per_line)]
    return "\n".join(lines)


def _format_search_item(post: dict, page: int, index: int, total: int) -> str:
    score = post.get("score", 0)
    fav = post.get("fav_count", 0)
    rating = post.get("rating", "?")
    ext = post.get("file_ext", "?")
    return (
        f"🔍 搜索结果 (第{page}页，第{index}/{total}条)\n"
        f"#{post['id']} | ⭐{score} ❤️{fav} | {rating} | {ext}\n"
        f"🔗 https://danbooru.donmai.us/posts/{post['id']}"
    )


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_post(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not args:
            yield event.plain_result(MESSAGES["missing_post_id"])
            return

        try:
            post_id = int(args.strip())
        except ValueError:
            yield event.plain_result(MESSAGES["invalid_post_id"])
            return

        response = await ctx.services.posts.get(post_id)
        if not response.success:
            yield event.plain_result(MESSAGES["post_fetch_failed"])
            return

        post = response.data
        if _only_image(ctx):
            url = _select_image_url(ctx, post)
            chain = _build_image_chain([url]) if url else None
            if chain:
                yield chain
                return
        tags_text = _format_tags(ctx, post.get("tag_string", ""))
        tag_line = f"🏷️ 标签: {tags_text}" if tags_text else "🏷️ 标签: (已隐藏)"
        info = f"""📸 帖子 #{post['id']}

⭐ 分数: {post.get('score', 0)} (⬆️{post.get('up_score', 0)} ⬇️{post.get('down_score', 0)})
❤️ 收藏: {post.get('fav_count', 0)}
📐 尺寸: {post.get('image_width', 0)}x{post.get('image_height', 0)}
🗂️ 格式: {post.get('file_ext', 'unknown')}
🔞 分级: {post.get('rating', 'unknown')}

{tag_line}

🔗 链接: https://danbooru.donmai.us/posts/{post['id']}
"""
        if _show_preview(ctx):
            url = _select_image_url(ctx, post)
            chain = _build_text_image_chain(info, url)
            if chain:
                yield chain
                return
        yield event.plain_result(info)

    async def cmd_posts(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        parsed = ctx.parser.parse_args(args)
        raw_tags = " ".join(parsed.positional) if parsed.positional else None
        is_id_search = bool(parsed.positional) and len(parsed.positional) == 1 and parsed.positional[0].isdigit()
        if is_id_search:
            tags = f"id:{parsed.positional[0]}"
        else:
            tags = _apply_filters(ctx, raw_tags)
        page = int(parsed.flags.get("page", 1))
        default_limit = 5
        if ctx.config:
            default_limit = ctx.config.display.search_limit or default_limit
        if default_limit <= 0:
            default_limit = 5
        limit = min(int(parsed.flags.get("limit", default_limit)), 20)
        limit = _apply_limit(ctx, limit)

        response = await ctx.services.posts.list(tags=tags, page=page, limit=limit)
        if not response.success:
            yield event.plain_result(MESSAGES["posts_search_failed"])
            return

        posts = response.data
        if not posts:
            yield event.plain_result(MESSAGES["posts_not_found"])
            return

        if _only_image(ctx):
            urls = [_select_image_url(ctx, post) for post in posts]
            chain = _build_image_chain(urls)
            if chain:
                yield chain
                return

        if _show_preview(ctx):
            total = len(posts)
            for idx, post in enumerate(posts, 1):
                text = _format_search_item(post, page, idx, total)
                url = _select_image_url(ctx, post)
                chain = _build_text_image_chain(text, url)
                if chain:
                    yield chain
                else:
                    yield event.plain_result(text)
            return

        result_lines = [f"🔍 搜索结果 (第{page}页，共{len(posts)}条)\n"]
        for post in posts:
            score = post.get('score', 0)
            fav = post.get('fav_count', 0)
            rating = post.get('rating', '?')
            result_lines.append(
                f"#{post['id']} | ⭐{score} ❤️{fav} | {rating} | {post.get('file_ext', '?')}"
            )
        result_lines.append("\n🔍 使用 `/danbooru post <id>` 查看详情")
        yield event.plain_result("\n".join(result_lines))

    async def cmd_random(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        tags = _apply_filters(ctx, args.strip()) if args else _apply_filters(ctx, None)
        response = await ctx.services.posts.random(tags=tags)
        if not response.success:
            yield event.plain_result(MESSAGES["random_failed"])
            return

        post = response.data
        if _only_image(ctx):
            url = _select_image_url(ctx, post)
            chain = _build_image_chain([url]) if url else None
            if chain:
                yield chain
                return
        info = f"""🎲 随机帖子 #{post['id']}

⭐ 分数: {post.get('score', 0)}
❤️ 收藏: {post.get('fav_count', 0)}
🔞 分级: {post.get('rating', 'unknown')}

🔗 链接: https://danbooru.donmai.us/posts/{post['id']}
"""
        if _show_preview(ctx):
            url = _select_image_url(ctx, post)
            chain = _build_text_image_chain(info, url)
            if chain:
                yield chain
                return
        yield event.plain_result(info)

    async def cmd_popular(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        parsed = ctx.parser.parse_args(args)
        date = parsed.positional[0] if parsed.positional else None
        scale = parsed.flags.get("scale", "day")

        response = await ctx.services.explore.popular(date=date, scale=scale)
        if not response.success:
            yield event.plain_result(MESSAGES["popular_failed"])
            return

        posts = response.data
        if not posts:
            yield event.plain_result(MESSAGES["popular_empty"])
            return

        result_lines = [f"🔥 热门帖子 ({scale})\n"]
        for i, post in enumerate(posts[:10], 1):
            score = post.get('score', 0)
            fav = post.get('fav_count', 0)
            result_lines.append(f"{i}. #{post['id']} | ⭐{score} ❤️{fav}")

        yield event.plain_result("\n".join(result_lines))

    return {
        "post": cmd_post,
        "posts": cmd_posts,
        "random": cmd_random,
        "popular": cmd_popular,
    }
