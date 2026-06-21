from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, cast

from ..errors import ProviderError
from .base import ModelRequest, ModelResponse, Usage

_JSON_FENCE: Final[re.Pattern[str]] = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True, slots=True)
class ScriptedTurn:
    match: str
    response: ModelResponse


class MockProvider:
    name: str
    _model: str
    scripted: list[ScriptedTurn]
    call_log: list[ModelRequest]
    default_response: ModelResponse
    fail_after: int

    def __init__(
        self,
        model: str = "mock",
        scripted: list[ScriptedTurn] | None = None,
        default_response: ModelResponse | None = None,
    ) -> None:
        self.name = "mock"
        self._model = model
        self.scripted = list(scripted) if scripted else []
        self.call_log = []
        self.default_response = (
            default_response
            if default_response is not None
            else ModelResponse(
                text='{"edits":[],"reasoning":"mock no-op"}',
                usage=Usage.zero(),
                model=model,
                latency_ms=0,
                raw={},
            )
        )
        self.fail_after = -1

    @property
    def model(self) -> str:
        return self._model

    def script(self, turn: ScriptedTurn) -> None:
        self.scripted.append(turn)

    def complete(self, request: ModelRequest) -> ModelResponse:
        self.call_log.append(request)
        if 0 <= self.fail_after < len(self.call_log):
            raise ProviderError("mock provider exhausted", code="mock_exhausted")
        idx = len(self.call_log) - 1
        if self.scripted and 0 <= idx < len(self.scripted):
            return self.scripted[idx].response
        for turn in self.scripted:
            if turn.match in request.prompt or turn.match in request.system:
                return turn.response
        return self.default_response

    def health(self) -> Mapping[str, str]:
        return {
            "provider": self.name,
            "model": self._model,
            "scripted": str(len(self.scripted)),
            "calls": str(len(self.call_log)),
        }


def make_json_response(payload: Mapping[str, object], *, model: str = "mock") -> ModelResponse:
    text = json.dumps(dict(payload), sort_keys=True)
    return ModelResponse(
        text=f"```json\n{text}\n```",
        usage=Usage(input_tokens=len(text) // 4, output_tokens=len(text) // 4, cost_usd=0.0),
        model=model,
        latency_ms=1,
        raw={},
    )


def extract_json(text: str) -> dict[str, object]:
    fence = _JSON_FENCE.search(text)
    if fence:
        loaded = json.loads(fence.group(1))
        if isinstance(loaded, dict):
            return cast(dict[str, object], loaded)
        raise ProviderError("json fence was not an object", code="not_object")
    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        loaded = json.loads(text[start : end + 1])
        if isinstance(loaded, dict):
            return cast(dict[str, object], loaded)
        raise ProviderError("json region was not an object", code="not_object")
    raise ProviderError("response contained no JSON object", code="no_json", context={"snippet": text[:200]})
