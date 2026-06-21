from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Final, cast

from ..errors import ProviderError
from .base import ModelRequest, ModelResponse, Usage, estimate_tokens, now_ms

_PRICING_USD_PER_1K: Final[Mapping[str, tuple[float, float]]] = {
    "gpt-4.1": (0.0025, 0.01),
    "gpt-4.1-mini": (0.0004, 0.0016),
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "o3": (0.01, 0.04),
    "o4-mini": (0.0011, 0.0044),
}

_DEFAULT_PRICING: Final[tuple[float, float]] = _PRICING_USD_PER_1K["gpt-4.1"]


def _openai_price(model: str) -> tuple[float, float]:
    return _PRICING_USD_PER_1K.get(model, _DEFAULT_PRICING)


def _import_openai() -> Any:
    try:
        import openai as _sdk
    except ImportError as exc:
        raise ProviderError(
            "openai SDK not installed; run `pip install openai`",
            code="missing_dependency",
            context={"package": "openai"},
        ) from exc
    return cast(Any, _sdk)


class OpenAIProvider:
    name: str
    _model: str
    _max_retries: int

    def __init__(self, model: str = "gpt-4.1", max_retries: int = 3) -> None:
        self.name = "openai"
        self._model = model
        self._max_retries = max(0, int(max_retries))

    @property
    def model(self) -> str:
        return self._model

    def complete(self, request: ModelRequest) -> ModelResponse:
        sdk = _import_openai()
        api_key = request.metadata.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ProviderError("OPENAI_API_KEY is not set", code="missing_api_key")
        client = sdk.OpenAI(api_key=api_key, max_retries=self._max_retries)
        started = now_ms()
        model_name = request.model or self._model
        try:
            response = client.chat.completions.create(
                model=model_name,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=[
                    {"role": "system", "content": request.system or ""},
                    {"role": "user", "content": request.prompt},
                ],
            )
        except (
            sdk.APIError,
            sdk.APIConnectionError,
            sdk.RateLimitError,
            OSError,
            TimeoutError,
        ) as exc:
            raise ProviderError(
                f"openai call failed: {exc}",
                code="api_failure",
                context={"model": model_name},
            ) from exc
        text = ""
        match response.choices:
            case [first, *_]:
                text = str(getattr(first.message, "content", "") or "")
            case _:
                pass
        usage_obj = getattr(response, "usage", None)
        usage_in = int(getattr(usage_obj, "prompt_tokens", 0))
        usage_out = int(getattr(usage_obj, "completion_tokens", 0))
        if usage_in == 0:
            usage_in = estimate_tokens(request.prompt)
        if usage_out == 0:
            usage_out = estimate_tokens(text)
        in_price, out_price = _openai_price(model_name)
        cost = (usage_in / 1000.0) * in_price + (usage_out / 1000.0) * out_price
        return ModelResponse(
            text=text,
            usage=Usage(input_tokens=usage_in, output_tokens=usage_out, cost_usd=cost),
            model=model_name,
            latency_ms=now_ms() - started,
            raw={"id": ""},
        )

    def health(self) -> Mapping[str, str]:
        return {"provider": self.name, "model": self._model}
