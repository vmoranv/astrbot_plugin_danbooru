"""
Shared command context.
"""

from dataclasses import dataclass
from typing import Dict

from core.client import DanbooruClient
from core.config import PluginConfig
from services.registry import ServiceRegistry
from .parser import CommandParser


@dataclass
class CommandContext:
    client: DanbooruClient
    config: PluginConfig
    services: ServiceRegistry
    help_messages: Dict[str, str]
    parser: CommandParser
