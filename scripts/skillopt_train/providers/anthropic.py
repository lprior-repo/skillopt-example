from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Final, cast

from ..errors import ProviderError
from .base import ModelRequest, ModelResponse, Usage, estimate_tokens, now_ms

_PRICING_USD_PER_1K: Final[Mapping[str, tuple[float, float]]] = {
    "claude-opus-4-1": (0.015, 0.075),
    "claude-sonnet-4-5": (0.003, 0.015),
    "claude-haiku-4-5": (0.0008, 0.004),
    "claude-3-5-sonnet": (0.003, 0.015),
    "claude-3-5-haiku": (0.0008, 0.004),
}

_DEFAULT_PRICING: Final[tuple[float, float]] = _PRICING_USD_PER_1K["claude-sonnet-4-5"]


def _anthropic_price(model: str) -> tuple[float, float]:
    return _PRICING_USD_PER_1K.get(model, _DEFAULT_PRICING)


def _import_anthropic() -> Any:
    try:
        import anthropic as _sdk
    except ImportError as exc:
        raise ProviderError(
            "anthropic SDK not installed; run `pip install anthropic`",
            code="missing_dependency",
            context={"package": "anthropic"},
        ) from exc
    return cast(Any, _sdk)


class AnthropicProvider:
    name: str
    _model: str
    _max_retries: int

    def __init__(self, model: str = "claude-sonnet-4-5", max_retries: int = 3) -> None:
        self.name = "anthropic"
        self._model = model
        self._max_retries = max(0, int(max_retries))

    @property
    def model(self) -> str:
        return self._model

    def complete(self, request: ModelRequest) -> ModelResponse:
        sdk = _import_anthropic()
        api_key = request.metadata.get("api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ProviderError("ANTHROPIC_API_KEY is not set", code="missing_api_key")
        client = sdk.Anthropic(api_key=api_key)
        started = now_ms()
        model_name = request.model or self._model
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = client.messages.create(
                    model=model_name,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    system=request.system or "",
                    messages=[{"role": "user", "content": request.prompt}],
                )
                text_parts: list[str] = []
                for block in response.content:
                    if getattr(block, "type", "") == "text":
                        text_parts.append(getattr(block, "text", ""))
                text = "\n".join(text_parts)
                usage_in = int(getattr(response.usage, "input_tokens", 0))
                usage_out = int(getattr(response.usage, "output_tokens", 0))
                if usage_in == 0:
                    usage_in = estimate_tokens(request.prompt)
                if usage_out == 0:
                    usage_out = estimate_tokens(text)
                in_price, out_price = _anthropic_price(model_name)
                cost = (usage_in / 1000.0) * in_price + (usage_out / 1000.0) * out_price
                return ModelResponse(
                    text=text,
                    usage=Usage(input_tokens=usage_in, output_tokens=usage_out, cost_usd=cost),
                    model=model_name,
                    latency_ms=now_ms() - started,
                    raw={"id": ""},
                )
            except ProviderError:
                raise
            except (
                sdk.APIError,
                sdk.APIConnectionError,
                sdk.RateLimitError,
                OSError,
                TimeoutError,
            ) as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    break
        raise ProviderError(
            f"anthropic call failed after {self._max_retries + 1} attempts: {last_exc}",
            code="api_failure",
            context={"model": model_name},
        ) from last_exc

    def health(self) -> Mapping[str, str]:
        return {"provider": self.name, "model": self._model}
