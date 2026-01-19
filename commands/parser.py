"""
Command parsing helpers.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import inspect
import json
import shlex


@dataclass
class ParsedArgs:
    positional: List[str]
    flags: Dict[str, Any]


class CommandParser:
    """Command argument parser and formatter."""

    def split_args(self, message: str) -> List[str]:
        if not message:
            return []
        try:
            return shlex.split(message)
        except ValueError:
            return message.split()

    def parse_tokens(self, tokens: List[str]) -> ParsedArgs:
        positional: List[str] = []
        flags: Dict[str, Any] = {}
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.startswith("--"):
                key = token[2:]
                if "=" in key:
                    flag_key, flag_value = key.split("=", 1)
                    flags[flag_key] = flag_value
                    i += 1
                elif i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                    flags[key] = tokens[i + 1]
                    i += 2
                else:
                    flags[key] = True
                    i += 1
            else:
                positional.append(token)
                i += 1
        return ParsedArgs(positional=positional, flags=flags)

    def parse_args(self, message: str) -> ParsedArgs:
        return self.parse_tokens(self.split_args(message))

    def parse_value(self, value: str) -> Any:
        if value == "":
            return ""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def parse_kv_pairs(self, items: List[str]) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        for item in items:
            if "=" not in item:
                raise ValueError(f"Bad param: {item} (expected key=value)")
            key, value = item.split("=", 1)
            params[key] = self.parse_value(value)
        return params

    def format_response_data(self, data: Any, max_chars: int = 1200) -> str:
        if data is None:
            return "(empty response)"
        if isinstance(data, str):
            text = data
        else:
            text = json.dumps(data, ensure_ascii=False, indent=2)
        if len(text) > max_chars:
            return text[:max_chars] + "\n... (truncated)"
        return text

    @staticmethod
    def list_service_methods(service: Any) -> List[str]:
        methods: List[str] = []
        for name, member in inspect.getmembers(service, predicate=callable):
            if name.startswith("_"):
                continue
            methods.append(name)
        return sorted(set(methods))
