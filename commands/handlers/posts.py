"""
Post command handlers.
"""

from typing import Dict, AsyncIterator, Iterable, List, Optional
import random

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
VIDEO_EXTS = {"mp4", "webm", "zip", "ugoira"}


def _is_video_post(post: dict) -> bool:
    ext = (post.get("file_ext") or "").lower()
    return ext in VIDEO_EXTS


def _url_has_ext(url: str, exts: set[str]) -> bool:
    lower = url.lower()
    return any(lower.endswith(f".{ext}") for ext in exts)


def _pick_url(post: dict, keys: Iterable[str], forbid_exts: Optional[set[str]] = None) -> Optional[str]:
    for key in keys:
        url = post.get(key)
        if not url:
            continue
        if forbid_exts and _url_has_ext(url, forbid_exts):
            continue
        return url
    return None


def _select_image_url(ctx: CommandContext, post: dict) -> Optional[str]:
    if _is_video_post(post):
        return _pick_url(
            post,
            ("preview_file_url", "large_file_url", "file_url"),
            forbid_exts=VIDEO_EXTS,
        )
    size = ctx.config.display.preview_size if ctx.config else "preview"
    if size == "original":
        return _pick_url(post, ("file_url", "large_file_url", "preview_file_url"))
    if size == "sample":
        return _pick_url(post, ("large_file_url", "file_url", "preview_file_url"))
    return _pick_url(post, ("preview_file_url", "large_file_url", "file_url"))


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


def _shuffle_posts(posts: Iterable[dict]) -> List[dict]:
    items = list(posts or [])
    random.shuffle(items)
    return items


def _pick_random_posts(posts: Iterable[dict], limit: int) -> List[dict]:
    items = list(posts or [])
    if limit <= 0 or len(items) <= limit:
        return items
    return random.sample(items, k=limit)
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


async def _is_image_accessible(ctx: CommandContext, url: str) -> bool:
    if not url or not ctx.client:
        return False
    headers = {
        "Range": "bytes=0-0",
        "User-Agent": "AstrBot-Danbooru-Plugin/1.0",
    }
    if ctx.config:
        headers["Referer"] = ctx.config.api.base_url
    try:
        session = await ctx.client._get_session()
        async with session.get(url, headers=headers) as resp:
            return resp.status < 400
    except Exception:
        return False


def _format_search_item(ctx: CommandContext, post: dict, page: int, index: int, total: int) -> str:
    score = post.get("score", 0)
    fav = post.get("fav_count", 0)
    rating = post.get("rating", "?")
    ext = post.get("file_ext", "?")
    tag_string = post.get("tag_string", "")
    tags_text = _format_tags(ctx, tag_string)
    tag_line = ""
    if tag_string:
        tag_line = f"\n🏷️ 标签: {tags_text}" if tags_text else "\n🏷️ 标签: (已隐藏)"
    return (
        f"🔍 搜索结果 (第{page}页，第{index}/{total}条)\n"
        f"#{post['id']} | ⭐{score} ❤️{fav} | {rating} | {ext}"
        f"{tag_line}\n"
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
        video_line = ""
        if _is_video_post(post):
            video_url = post.get("file_url")
            if video_url:
                video_line = f"\n🎞️ 原视频: {video_url}"
        info = f"""📸 帖子 #{post['id']}

⭐ 分数: {post.get('score', 0)} (⬆️{post.get('up_score', 0)} ⬇️{post.get('down_score', 0)})
❤️ 收藏: {post.get('fav_count', 0)}
📐 尺寸: {post.get('image_width', 0)}x{post.get('image_height', 0)}
🗂️ 格式: {post.get('file_ext', 'unknown')}
🔞 分级: {post.get('rating', 'unknown')}

{tag_line}

🔗 链接: https://danbooru.donmai.us/posts/{post['id']}{video_line}
"""
        if _show_preview(ctx):
            url = _select_image_url(ctx, post)
            if url and await _is_image_accessible(ctx, url):
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
        requested = int(parsed.flags.get("limit", default_limit))
        if ctx.config:
            limit = ctx.config.resolve_batch_limit(requested, default_limit, 20)
        else:
            limit = min(requested, 20)
        limit = _apply_limit(ctx, limit)
        pool_limit = min(max(limit * 5, limit), 20)
        if ctx.config and ctx.config.filter.max_results:
            pool_limit = min(pool_limit, int(ctx.config.filter.max_results))
        if pool_limit < limit:
            pool_limit = limit

        response = await ctx.services.posts.list(tags=tags, page=page, limit=pool_limit)
        if not response.success:
            yield event.plain_result(MESSAGES["posts_search_failed"])
            return

        posts = response.data
        if not posts:
            yield event.plain_result(MESSAGES["posts_not_found"])
            return

        show_preview = _show_preview(ctx)
        only_image = _only_image(ctx)

        if show_preview or only_image:
            selected: List[tuple[dict, str, int]] = []
            max_pages = 3

            for page_offset in range(max_pages):
                page_num = page + page_offset
                if page_offset == 0:
                    page_posts = posts or []
                else:
                    response = await ctx.services.posts.list(
                        tags=tags,
                        page=page_num,
                        limit=pool_limit,
                    )
                    if not response.success:
                        yield event.plain_result(MESSAGES["posts_search_failed"])
                        return
                    page_posts = response.data or []
                if not page_posts:
                    break
                page_posts = _shuffle_posts(page_posts)
                for post in page_posts:
                    url = _select_image_url(ctx, post)
                    if not url:
                        continue
                    if not await _is_image_accessible(ctx, url):
                        continue
                    selected.append((post, url, page_num))
                    if len(selected) >= limit:
                        break
                if len(selected) >= limit:
                    break

            if not selected:
                yield event.plain_result(MESSAGES["posts_not_found"])
                return

            if only_image:
                urls = [url for _, url, _ in selected[:limit]]
                chain = _build_image_chain(urls)
                if chain:
                    yield chain
                return

            total = len(selected)
            for idx, (post, url, page_num) in enumerate(selected[:limit], 1):
                text = _format_search_item(ctx, post, page_num, idx, total)
                chain = _build_text_image_chain(text, url)
                if chain:
                    yield chain
                else:
                    yield event.plain_result(text)
            return

        selected_posts = _pick_random_posts(posts, limit)
        result_lines = [
            f"🔍 搜索结果 (第{page}页，随机{len(selected_posts)}/{len(posts)}条)\n"
        ]
        for post in selected_posts:
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
            if url and await _is_image_accessible(ctx, url):
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
        default_limit = 5
        if ctx.config:
            limit = ctx.config.resolve_batch_limit(None, default_limit, 20)
        else:
            limit = min(default_limit, 20)
        limit = _apply_limit(ctx, limit)

        show_preview = _show_preview(ctx)
        only_image = _only_image(ctx)

        if show_preview or only_image:
            candidates = _shuffle_posts(posts)
            selected: List[tuple[dict, str]] = []
            for post in candidates:
                url = _select_image_url(ctx, post)
                if not url:
                    continue
                if not await _is_image_accessible(ctx, url):
                    continue
                selected.append((post, url))
                if len(selected) >= limit:
                    break

            if selected:
                if only_image:
                    urls = [url for _, url in selected[:limit]]
                    chain = _build_image_chain(urls)
                    if chain:
                        yield chain
                    return

                total = len(selected[:limit])
                for idx, (post, url) in enumerate(selected[:limit], 1):
                    score = post.get("score", 0)
                    fav = post.get("fav_count", 0)
                    rating = post.get("rating", "?")
                    tags_text = _format_tags(ctx, post.get("tag_string", ""))
                    lines = [
                        f"🔥 热门帖子 ({scale}，第{idx}/{total}条)",
                        f"#{post['id']} | ⭐{score} ❤️{fav} | {rating}",
                    ]
                    if tags_text:
                        lines.append(f"🏷️ 标签: {tags_text}")
                    lines.append(
                        f"🔗 https://danbooru.donmai.us/posts/{post['id']}"
                    )
                    text = "\n".join(lines)
                    chain = _build_text_image_chain(text, url)
                    if chain:
                        yield chain
                    else:
                        yield event.plain_result(text)
                return

            if only_image:
                yield event.plain_result(MESSAGES["popular_empty"])
                return

        selected_posts = _pick_random_posts(posts, limit)
        result_lines = [
            f"🔥 热门帖子 ({scale}) 随机{len(selected_posts)}/{len(posts)}条\n"
        ]
        for i, post in enumerate(selected_posts, 1):
            score = post.get("score", 0)
            fav = post.get("fav_count", 0)
            result_lines.append(f"{i}. #{post['id']} | ⭐{score} ❤️{fav}")

        yield event.plain_result("\n".join(result_lines))

    return {
        "post": cmd_post,
        "posts": cmd_posts,
        "random": cmd_random,
        "popular": cmd_popular,
    }
