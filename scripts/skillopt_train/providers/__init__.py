from __future__ import annotations

from typing import TYPE_CHECKING, Final

from .base import ModelProvider, ModelRequest, ModelResponse, Usage, estimate_tokens, load_provider, now_ms
from .mock import MockProvider, ScriptedTurn, extract_json, make_json_response

if TYPE_CHECKING:
    from .anthropic import AnthropicProvider
    from .openai import OpenAIProvider
    from .opencode import OpencodeProvider

_LAZY_PROVIDER_MODULES: Final[dict[str, str]] = {
    "AnthropicProvider": ".anthropic",
    "OpenAIProvider": ".openai",
    "OpencodeProvider": ".opencode",
}

__all__ = [
    "AnthropicProvider",
    "MockProvider",
    "ModelProvider",
    "ModelRequest",
    "ModelResponse",
    "OpenAIProvider",
    "OpencodeProvider",
    "ScriptedTurn",
    "Usage",
    "estimate_tokens",
    "extract_json",
    "load_provider",
    "make_json_response",
    "now_ms",
]


def __getattr__(name: str) -> object:
    module_rel = _LAZY_PROVIDER_MODULES.get(name)
    if module_rel is not None:
        import importlib

        module = importlib.import_module(module_rel, __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals().keys(), *__all__})
