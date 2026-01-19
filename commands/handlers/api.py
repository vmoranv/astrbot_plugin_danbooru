"""
Raw API command handler.
"""

from typing import Dict, AsyncIterator, Any
import json

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler
from ...core.http_utils import RequestOptions


MESSAGES = {
    "client_not_ready": "❌ 客户端未初始化，请稍后再试",
    "missing_endpoint": "❌ 请提供 endpoint\n用法: `/danbooru api <METHOD> <endpoint>`",
    "bad_param": "❌ {error}",
    "bad_json": "❌ --json 解析失败，请使用引号包裹有效 JSON",
    "llm_tools_disabled": "❌ 当前配置已禁用 LLM 工具入口",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_api(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not ctx.client:
            yield event.plain_result(MESSAGES["client_not_ready"])
            return
        if ctx.config and not ctx.config.enable_llm_tools:
            yield event.plain_result(MESSAGES["llm_tools_disabled"])
            return

        tokens = ctx.parser.split_args(args)
        if not tokens:
            yield event.plain_result(ctx.help_messages["api"])
            return

        method = tokens[0].upper()
        if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            if len(tokens) < 2:
                yield event.plain_result(MESSAGES["missing_endpoint"])
                return
            endpoint = tokens[1]
            rest = tokens[2:]
        else:
            method = "GET"
            endpoint = tokens[0]
            rest = tokens[1:]

        parsed = ctx.parser.parse_tokens(rest)
        flags = parsed.flags
        positional = parsed.positional

        try:
            kv_params = ctx.parser.parse_kv_pairs(positional) if positional else {}
        except ValueError as exc:
            yield event.plain_result(MESSAGES["bad_param"].format(error=exc))
            return

        json_body: Any = None
        if "json" in flags:
            try:
                json_body = json.loads(flags["json"])
            except json.JSONDecodeError:
                yield event.plain_result(MESSAGES["bad_json"])
                return

        params = None
        body = None

        if method in {"GET", "DELETE"}:
            params = kv_params
            if json_body is not None:
                params = json_body if isinstance(json_body, dict) else {"data": json_body}
        else:
            body = kv_params
            if json_body is not None:
                body = json_body

        if flags.get("params"):
            params = kv_params if json_body is None else json_body
            body = None
        if flags.get("body"):
            body = kv_params if json_body is None else json_body
            params = None

        auth = str(flags.get("auth", "header")).lower()
        use_auth = auth not in {"none", "false", "0", "no"}
        auth_method = auth if auth in {"header", "params"} else "header"
        response_format = str(flags.get("format", "json")).lower()
        if response_format not in {"json", "xml"}:
            response_format = "json"

        use_cache = not bool(flags.get("no-cache", False))
        options = RequestOptions(
            use_auth=use_auth,
            auth_method=auth_method,
            response_format=response_format,
        )

        response = await ctx.client.request(
            method,
            endpoint,
            params=params,
            json_data=body,
            options=options,
            use_cache=use_cache,
        )

        output = ctx.parser.format_response_data(response.data)
        yield event.plain_result(f"✅ {method} {endpoint} ({response.status_code})\n{output}")

    return {"api": cmd_api}
