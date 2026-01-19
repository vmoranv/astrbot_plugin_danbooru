"""
Service method call handler.
"""

from typing import Dict, AsyncIterator, List, Any
import inspect
import json

from astrbot.api.event import AstrMessageEvent, MessageEventResult

from ..context import CommandContext
from ..types import Handler
from core.models import APIResponse


MESSAGES = {
    "services_not_ready": "❌ 服务未初始化，请稍后再试",
    "missing_service": "❌ 未知服务: {service}",
    "missing_methods": "❌ 请提供服务名\n用法: `/danbooru call methods <service>`",
    "missing_method": "❌ 请提供方法名\n可用方法: {methods}",
    "method_not_found": "❌ 未找到方法: {service}.{method}",
    "bad_param": "❌ {error}",
    "bad_args": "❌ --args 需要是 JSON 数组",
    "bad_json": "❌ --json 解析失败，请使用引号包裹有效 JSON",
    "call_failed": "❌ 调用失败",
    "llm_tools_disabled": "❌ 当前配置已禁用 LLM 工具入口",
}


def register(ctx: CommandContext) -> Dict[str, Handler]:
    async def cmd_call(event: AstrMessageEvent, args: str) -> AsyncIterator[MessageEventResult]:
        if not ctx.services or not ctx.services.service_map:
            yield event.plain_result(MESSAGES["services_not_ready"])
            return
        if ctx.config and not ctx.config.enable_llm_tools:
            yield event.plain_result(MESSAGES["llm_tools_disabled"])
            return

        tokens = ctx.parser.split_args(args)
        if not tokens:
            yield event.plain_result(ctx.help_messages["call"])
            return

        if tokens[0] in {"services", "service", "list"}:
            names = sorted(set(ctx.services.service_map.keys()))
            yield event.plain_result("🧩 可用服务: " + ", ".join(names))
            return

        if tokens[0] == "methods":
            if len(tokens) < 2:
                yield event.plain_result(MESSAGES["missing_methods"])
                return
            service_name = tokens[1]
            service = ctx.services.service_map.get(service_name)
            if not service:
                yield event.plain_result(MESSAGES["missing_service"].format(service=service_name))
                return
            methods = ctx.parser.list_service_methods(service)
            yield event.plain_result(f"🧩 {service_name} 可用方法:\n" + ", ".join(methods))
            return

        service_name = tokens[0]
        service = ctx.services.service_map.get(service_name)
        if not service:
            names = ", ".join(sorted(set(ctx.services.service_map.keys())))
            yield event.plain_result(f"❌ 未知服务: {service_name}\n可用服务: {names}")
            return

        if len(tokens) < 2:
            methods = ctx.parser.list_service_methods(service)
            yield event.plain_result(MESSAGES["missing_method"].format(methods=", ".join(methods)))
            return

        method_name = tokens[1]
        if method_name == "methods":
            methods = ctx.parser.list_service_methods(service)
            yield event.plain_result(f"🧩 {service_name} 可用方法:\n" + ", ".join(methods))
            return

        method = getattr(service, method_name, None)
        if not callable(method) or method_name.startswith("_"):
            yield event.plain_result(MESSAGES["method_not_found"].format(service=service_name, method=method_name))
            return

        parsed = ctx.parser.parse_tokens(tokens[2:])
        flags = parsed.flags
        raw_positional = parsed.positional

        pos_args: List[Any] = []
        kv_items: List[str] = []
        for item in raw_positional:
            if "=" in item:
                kv_items.append(item)
            else:
                pos_args.append(ctx.parser.parse_value(item))

        try:
            kwargs = ctx.parser.parse_kv_pairs(kv_items) if kv_items else {}
        except ValueError as exc:
            yield event.plain_result(MESSAGES["bad_param"].format(error=exc))
            return

        if "args" in flags:
            try:
                extra_args = json.loads(flags["args"])
                if not isinstance(extra_args, list):
                    raise ValueError
                pos_args.extend(extra_args)
            except Exception:
                yield event.plain_result(MESSAGES["bad_args"])
                return

        if "json" in flags:
            try:
                extra = json.loads(flags["json"])
            except json.JSONDecodeError:
                yield event.plain_result(MESSAGES["bad_json"])
                return

            if isinstance(extra, dict):
                kwargs.update(extra)
            elif isinstance(extra, list):
                pos_args.extend(extra)
            else:
                kwargs["data"] = extra

        if inspect.iscoroutinefunction(method):
            result = await method(*pos_args, **kwargs)
        else:
            result = method(*pos_args, **kwargs)

        if isinstance(result, APIResponse):
            if not result.success:
                yield event.plain_result(MESSAGES["call_failed"])
                return
            output = ctx.parser.format_response_data(result.data)
        else:
            output = ctx.parser.format_response_data(result)

        yield event.plain_result(f"✅ {service_name}.{method_name}\n{output}")

    return {"call": cmd_call}
