"""
Command handler registry.
"""

from typing import Dict, Callable, AsyncIterator

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from .context import CommandContext
from .handlers import (
    api as api_handlers,
    call as call_handlers,
    posts as posts_handlers,
    tags as tags_handlers,
    artists as artists_handlers,
    pools as pools_handlers,
    users as users_handlers,
    wiki as wiki_handlers,
    comments as comments_handlers,
    misc as misc_handlers,
    help as help_handlers,
)


Handler = Callable[[AstrMessageEvent, str], AsyncIterator[MessageEventResult]]


def build_handlers(ctx: CommandContext) -> Dict[str, Handler]:
    handlers: Dict[str, Handler] = {}
    handlers.update(help_handlers.register(ctx))
    handlers.update(posts_handlers.register(ctx))
    handlers.update(tags_handlers.register(ctx))
    handlers.update(artists_handlers.register(ctx))
    handlers.update(pools_handlers.register(ctx))
    handlers.update(users_handlers.register(ctx))
    handlers.update(wiki_handlers.register(ctx))
    handlers.update(comments_handlers.register(ctx))
    handlers.update(misc_handlers.register(ctx))
    handlers.update(api_handlers.register(ctx))
    handlers.update(call_handlers.register(ctx))
    return handlers
