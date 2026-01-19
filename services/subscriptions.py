"""Subscription storage and access helpers."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

from astrbot.api import sp

from events.event_bus import EventBus


class SubscriptionsService:
    """Manage group subscriptions for tags and daily popular posts."""

    _scope = "plugin"
    _scope_id = "danbooru"
    _key_prefix = "group:"

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._lock = asyncio.Lock()

    def _key(self, group_id: str) -> str:
        return f"{self._key_prefix}{group_id}"

    async def _ensure_group(
        self,
        group_id: str,
        platform: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        key = self._key(group_id)
        group = await sp.get_async(self._scope, self._scope_id, key, default=None)
        if not group:
            group = {
                "group_id": group_id,
                "platform": platform,
                "session_id": session_id,
                "tags": {},
                "popular": {"enabled": False, "last_sent": 0, "scale": "day"},
            }
        if platform:
            group["platform"] = platform
        if session_id:
            group["session_id"] = session_id
        if "tags" not in group:
            group["tags"] = {}
        if "popular" not in group:
            group["popular"] = {"enabled": False, "last_sent": 0, "scale": "day"}
        if "scale" not in group["popular"]:
            group["popular"]["scale"] = "day"
        await sp.put_async(self._scope, self._scope_id, key, group)
        return json.loads(json.dumps(group))

    async def list_groups(self) -> Dict[str, Any]:
        async with self._lock:
            prefs = await sp.range_get_async(self._scope, self._scope_id, None)
            groups: Dict[str, Any] = {}
            for pref in prefs:
                key = getattr(pref, "key", "")
                if not isinstance(key, str) or not key.startswith(self._key_prefix):
                    continue
                group_id = key[len(self._key_prefix):]
                value = getattr(pref, "value", {}) or {}
                group = value.get("val")
                if group:
                    groups[group_id] = json.loads(json.dumps(group))
            return groups

    async def list_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            key = self._key(group_id)
            group = await sp.get_async(self._scope, self._scope_id, key, default=None)
            return json.loads(json.dumps(group)) if group else None

    async def subscribe_tag(
        self,
        group_id: str,
        tag: str,
        platform: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            group = await self._ensure_group(group_id, platform=platform, session_id=session_id)
            tags = group["tags"]
            if tag not in tags:
                tags[tag] = {"last_post_id": None}
            await sp.put_async(self._scope, self._scope_id, self._key(group_id), group)
            return json.loads(json.dumps(group))

    async def unsubscribe_tag(self, group_id: str, tag: str) -> bool:
        async with self._lock:
            key = self._key(group_id)
            group = await sp.get_async(self._scope, self._scope_id, key, default=None)
            if not group:
                return False
            tags = group.get("tags", {})
            if tag not in tags:
                return False
            tags.pop(tag, None)
            await sp.put_async(self._scope, self._scope_id, key, group)
            return True

    async def update_last_post(self, group_id: str, tag: str, post_id: int) -> None:
        async with self._lock:
            group = await self._ensure_group(group_id)
            tags = group["tags"]
            tags.setdefault(tag, {})["last_post_id"] = post_id
            await sp.put_async(self._scope, self._scope_id, self._key(group_id), group)

    async def set_popular(
        self,
        group_id: str,
        enabled: bool,
        platform: Optional[str] = None,
        session_id: Optional[str] = None,
        scale: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            group = await self._ensure_group(group_id, platform=platform, session_id=session_id)
            group["popular"]["enabled"] = enabled
            if scale:
                group["popular"]["scale"] = scale
            await sp.put_async(self._scope, self._scope_id, self._key(group_id), group)
            return json.loads(json.dumps(group))

    async def update_popular_sent(self, group_id: str, timestamp: int) -> None:
        async with self._lock:
            group = await self._ensure_group(group_id)
            group["popular"]["last_sent"] = timestamp
            await sp.put_async(self._scope, self._scope_id, self._key(group_id), group)
