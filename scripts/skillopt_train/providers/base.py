from __future__ import annotations

import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Protocol

from ..errors import ProviderError


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cost_usd: float

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cost_usd=self.cost_usd + other.cost_usd,
        )

    @staticmethod
    def zero() -> Usage:
        return Usage(input_tokens=0, output_tokens=0, cost_usd=0.0)


@dataclass(frozen=True, slots=True)
class ModelRequest:
    prompt: str
    system: str
    model: str
    max_tokens: int
    temperature: float
    json_schema: Mapping[str, object] | None
    metadata: Mapping[str, str]

    @staticmethod
    def new(
        prompt: str,
        *,
        system: str = "",
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        json_schema: Mapping[str, object] | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> ModelRequest:
        return ModelRequest(
            prompt=prompt,
            system=system,
            model=model,
            max_tokens=max(64, int(max_tokens)),
            temperature=max(0.0, min(2.0, float(temperature))),
            json_schema=json_schema,
            metadata=dict(metadata) if metadata else {},
        )


@dataclass(frozen=True, slots=True)
class ModelResponse:
    text: str
    usage: Usage
    model: str
    latency_ms: int
    raw: Mapping[str, object]

    @property
    def ok(self) -> bool:
        return bool(self.text)


class ModelProvider(Protocol):
    name: str

    def complete(self, request: ModelRequest) -> ModelResponse: ...

    def health(self) -> Mapping[str, str]: ...


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


_USAGE_LINE: Final[re.Pattern[str]] = re.compile(
    r"usage[:\s]+input[=:]?\s*(\d+).*output[=:]?\s*(\d+)",
    re.IGNORECASE,
)


def parse_usage_block(stdout: str, stderr: str) -> Usage:
    for source in (stdout, stderr):
        match = _USAGE_LINE.search(source)
        if match:
            return Usage(
                input_tokens=int(match.group(1)),
                output_tokens=int(match.group(2)),
                cost_usd=0.0,
            )
    return Usage(input_tokens=estimate_tokens(stdout), output_tokens=0, cost_usd=0.0)


def now_ms() -> int:
    return int(time.time() * 1000)


def load_provider(spec: str) -> ModelProvider:
    from .anthropic import AnthropicProvider
    from .mock import MockProvider
    from .openai import OpenAIProvider
    from .opencode import OpencodeProvider

    name, _, arg = spec.partition(":")
    key = name.strip().lower()
    model_arg = arg.strip()
    match key:
        case "opencode":
            return OpencodeProvider(model=model_arg or "opencode default", timeout=900)
        case "anthropic":
            return AnthropicProvider(model=model_arg or "claude-sonnet-4-5")
        case "openai":
            return OpenAIProvider(model=model_arg or "gpt-4.1")
        case "mock" | "dryrun" | "dry-run":
            return MockProvider(model=model_arg or "mock")
        case _:
            raise ProviderError(
                f"unknown provider: {spec!r}",
                code="unknown_provider",
                context={"spec": spec},
            )
