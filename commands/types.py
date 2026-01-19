"""
Command typing helpers.
"""

from typing import AsyncIterator, Callable, TypeAlias

from astrbot.api.event import AstrMessageEvent, MessageEventResult

Handler: TypeAlias = Callable[[AstrMessageEvent, str], AsyncIterator[MessageEventResult]]
