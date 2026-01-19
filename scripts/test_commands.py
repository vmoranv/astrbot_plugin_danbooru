"""
Command coverage test for AstrBot Danbooru plugin.
Runs all registered /danbooru commands against testbooru.
"""

import argparse
import asyncio
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from typing import Iterable, List, Optional, Tuple

from core.client import DanbooruClient
from core.config import PluginConfig
from events.event_bus import EventBus
from services.registry import ServiceRegistry
from commands import HELP_MESSAGES, CommandContext, CommandParser, build_handlers

try:
    from main import DanbooruPlugin
except Exception:  # pragma: no cover - optional
    DanbooruPlugin = None


class FakeEvent:
    def __init__(self, message_str: str = ""):
        self.message_str = message_str

    def plain_result(self, text: str):
        return text


def _safe_text(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    return text.encode("ascii", errors="backslashreplace").decode("ascii")


RESULTS_ROOT = os.path.join(os.path.dirname(__file__), "test_results")


def _sanitize_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name)
    return safe or "unknown"


def _result_status(results: Iterable) -> str:
    if not results:
        return "empty"
    if any(_is_error(result) for result in results):
        return "error"
    if any(_is_warning(result) for result in results):
        return "warn"
    return "ok"


def _format_result_item(item) -> str:
    if isinstance(item, str):
        return item
    if _is_message_result(item):
        text = ""
        get_plain = getattr(item, "get_plain_text", None)
        if callable(get_plain):
            text = get_plain() or ""
        return f"<MessageResult text_len={len(text)}>"
    return repr(item)


def _format_results(results: Iterable) -> str:
    return "\n\n".join(_format_result_item(item) for item in results)


def _write_result(command: str, index: int, args: str, results: Iterable, status: str) -> None:
    folder = os.path.join(RESULTS_ROOT, _sanitize_name(command))
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"{index:02d}.txt")
    content = (
        f"command: {command}\n"
        f"args: {args}\n"
        f"status: {status}\n\n"
        f"{_format_results(results)}\n"
    )
    with open(filename, "w", encoding="utf-8") as handle:
        handle.write(content)


def _is_error(result) -> bool:
    return isinstance(result, str) and result.strip().startswith("❌")


def _is_warning(result) -> bool:
    return isinstance(result, str) and result.strip().startswith("⚠️")


def _is_message_result(result) -> bool:
    return not isinstance(result, str) and hasattr(result, "url_image")


def _summary(results: Iterable) -> str:
    if not results:
        return "(no output)"
    first = results[0]
    if isinstance(first, str):
        return first.splitlines()[0]
    return type(first).__name__


async def _collect(handler, event: FakeEvent, args: str) -> List:
    results = []
    async for result in handler(event, args):
        results.append(result)
    return results


async def _pick_first(response, field: Optional[str] = None):
    if not response.success or not isinstance(response.data, list) or not response.data:
        return None
    item = response.data[0]
    return item.get(field) if field else item


async def _collect_samples(services: ServiceRegistry):
    post = await _pick_first(await services.posts.list(limit=1))
    if not post:
        raise RuntimeError("No posts found on testbooru.")

    post_id = post.get("id")
    tag_name = (post.get("tag_string") or "").split()[0] if post.get("tag_string") else None
    user_id = post.get("uploader_id") or post.get("creator_id")
    user_name = post.get("uploader_name") or post.get("author")

    if not tag_name:
        tag_name = await _pick_first(await services.tags.list(limit=1), field="name")

    artist_name = await _pick_first(await services.artists.list(limit=1), field="name")
    pool = await _pick_first(await services.pools.list(limit=1))
    pool_id = pool.get("id") if pool else None
    pool_name = pool.get("name") if pool else None
    wiki_title = await _pick_first(await services.wiki.list(limit=1), field="title")
    if not user_id:
        user_id = await _pick_first(await services.users.list(limit=1), field="id")
    if not user_name:
        user_name = await _pick_first(await services.users.list(limit=1), field="name")

    missing = [
        name
        for name, value in {
            "post_id": post_id,
            "tag_name": tag_name,
            "artist_name": artist_name,
            "pool_id": pool_id,
            "pool_name": pool_name,
            "user_id": user_id,
            "user_name": user_name,
            "wiki_title": wiki_title,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing sample data: {', '.join(missing)}")

    return {
        "post_id": post_id,
        "tag_name": tag_name,
        "artist_name": artist_name,
        "pool_id": pool_id,
        "pool_name": pool_name,
        "user_id": user_id,
        "user_name": user_name,
        "wiki_title": wiki_title,
    }


async def run_tests(args: argparse.Namespace) -> int:
    try:
        from tqdm import tqdm
    except Exception:  # pragma: no cover - optional
        tqdm = None

    config = PluginConfig.from_dict({
        "api": {
            "base_url": args.base_url,
            "test_url": args.test_url,
            "use_test_server": args.use_test_server,
        },
        "auth": {
            "username": args.username,
            "api_key": args.api_key,
        },
        "display": {
            "only_image": args.only_image,
        },
    })

    event_bus = EventBus.get_instance()
    await event_bus.start()
    client = DanbooruClient(config=config, event_bus=event_bus)
    services = ServiceRegistry.build(client, event_bus)
    ctx = CommandContext(
        client=client,
        config=config,
        services=services,
        help_messages=HELP_MESSAGES,
        parser=CommandParser(),
    )
    handlers = build_handlers(ctx)

    try:
        samples = await _collect_samples(services)

        tag_prefix = samples["tag_name"][:2]
        tests: List[Tuple[str, str, bool]] = [
            ("help", "posts", False),
            ("post", str(samples["post_id"]), False),
            ("posts", samples["tag_name"], False),
            ("posts", str(samples["post_id"]), False),
            ("random", samples["tag_name"], False),
            ("popular", "", True),
            ("tag", samples["tag_name"], False),
            ("tags", samples["tag_name"], False),
            ("related", samples["tag_name"], True),
            ("artist", samples["artist_name"], False),
            ("artists", samples["artist_name"], False),
            ("pool", str(samples["pool_id"]), False),
            ("pools", samples["pool_name"], False),
            ("user", str(samples["user_id"]), False),
            ("favorites", str(samples["user_id"]), True),
            ("wiki", samples["wiki_title"], False),
            ("comments", str(samples["post_id"]), True),
            ("autocomplete", tag_prefix, True),
            ("count", samples["tag_name"], False),
            ("status", "", False),
            ("similar", str(samples["post_id"]), True),
            ("api", "posts?limit=1", False),
            ("call", "services", False),
            ("call", "methods posts", False),
            ("call", "posts list limit=1", False),
        ]

        failures = []
        step_index = 1
        progress = tqdm(tests, desc="Commands", unit="cmd") if tqdm else tests
        for name, command_args, allow_warn in progress:
            if tqdm:
                progress.set_postfix_str(name)
            handler = handlers.get(name)
            if not handler:
                _write_result(name, step_index, command_args, [], "missing handler")
                failures.append((name, command_args, "missing handler"))
                step_index += 1
                continue
            event = FakeEvent(f"/danbooru {name} {command_args}".strip())
            results = await _collect(handler, event, command_args)
            status = _result_status(results)
            _write_result(name, step_index, command_args, results, status)
            step_index += 1

            if not results:
                failures.append((name, command_args, "no output"))
                continue
            if status == "error":
                failures.append((name, command_args, _summary(results)))
                continue
            if not allow_warn and status == "warn":
                failures.append((name, command_args, _summary(results)))
                continue

        if DanbooruPlugin and not args.skip_main:
            plugin = DanbooruPlugin.__new__(DanbooruPlugin)
            plugin.config = config
            plugin.handlers = handlers
            plugin._handle_error = DanbooruPlugin._handle_error.__get__(plugin, DanbooruPlugin)

            event = FakeEvent(f"/danbooru {samples['tag_name']}")
            results = []
            async for result in DanbooruPlugin.cmd_main(plugin, event):
                results.append(result)
            status = _result_status(results)
            _write_result("cmd_main", step_index, samples["tag_name"], results, status)
            step_index += 1
            if not results:
                failures.append(("cmd_main", samples["tag_name"], "no output"))
            elif status == "error":
                failures.append(("cmd_main", samples["tag_name"], _summary(results)))

        if args.only_image:
            post_results = await _collect(handlers["post"], FakeEvent("/danbooru post"), str(samples["post_id"]))
            status = _result_status(post_results)
            _write_result("only_image", step_index, "post", post_results, status)
            step_index += 1
            if not any(_is_message_result(result) for result in post_results):
                failures.append(("only_image", "post", "not image-only output"))

        if failures:
            for name, command_args, reason in failures:
                safe_args = _safe_text(command_args)
                safe_reason = _safe_text(reason)
                print(f"FAIL | {name} {safe_args} -> {safe_reason}")
            return 1

        print("OK | All command handlers passed")
        return 0
    finally:
        await client.close()
        await event_bus.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test /danbooru command coverage")
    parser.add_argument("--base-url", default="https://danbooru.donmai.us")
    parser.add_argument("--test-url", default="https://testbooru.donmai.us")
    parser.add_argument("--use-test-server", action="store_true", default=True)
    parser.add_argument("--username", default=os.getenv("DANBOORU_USERNAME", ""))
    parser.add_argument("--api-key", default=os.getenv("DANBOORU_API_KEY", ""))
    parser.add_argument("--only-image", action="store_true")
    parser.add_argument("--skip-main", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_tests(parse_args())))
