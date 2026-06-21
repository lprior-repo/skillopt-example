from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict, cast

from .errors import ConfigError


class RubricDict(TypedDict, total=False):
    name: str
    description: str
    forbidden_tokens: dict[str, str]
    grade_issue_keys: list[str]
    grade_returncode_keys: list[str]
    success_threshold_hard: float
    max_examples: int


_DEFAULT_NAME: Final[str] = "default"
_DEFAULT_DESCRIPTION: Final[str] = ""
_DEFAULT_SUCCESS_THRESHOLD_HARD: Final[float] = 1.0
_DEFAULT_MAX_EXAMPLES: Final[int] = 5


def _as_str(value: object, default: str) -> str:
    match value:
        case str() as s:
            return s
        case bool() | int() | float():
            return str(value)
        case _:
            return default


def _as_float(value: object, default: float) -> float:
    match value:
        case bool():
            return float(int(value))
        case int() | float():
            return float(value)
        case str() as s:
            try:
                return float(s)
            except ValueError:
                return default
        case _:
            return default


def _as_int(value: object, default: int) -> int:
    match value:
        case bool():
            return int(value)
        case int():
            return int(value)
        case float():
            return int(value)
        case str() as s:
            try:
                return int(s)
            except ValueError:
                return default
        case _:
            return default


def _as_str_list(value: object) -> tuple[str, ...]:
    match value:
        case list() as items:
            return tuple(str(item) for item in items)
        case tuple() as items:
            return tuple(str(item) for item in items)
        case _:
            return ()


def _as_token_map(value: object) -> Mapping[str, str]:
    match value:
        case Mapping() as m:
            return cast(Mapping[str, str], {str(k): str(v) for k, v in m.items()})
        case _:
            return {}


@dataclass(frozen=True, slots=True)
class Rubric:
    name: str
    description: str
    forbidden_tokens: Mapping[str, str]
    grade_issue_keys: Sequence[str]
    grade_returncode_keys: Sequence[str]
    success_threshold_hard: float
    max_examples: int

    @staticmethod
    def default() -> Rubric:
        return Rubric(
            name=_DEFAULT_NAME,
            description=_DEFAULT_DESCRIPTION,
            forbidden_tokens={},
            grade_issue_keys=(),
            grade_returncode_keys=(),
            success_threshold_hard=_DEFAULT_SUCCESS_THRESHOLD_HARD,
            max_examples=_DEFAULT_MAX_EXAMPLES,
        )

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> Rubric:
        return Rubric(
            name=_as_str(data.get("name"), _DEFAULT_NAME),
            description=_as_str(data.get("description"), _DEFAULT_DESCRIPTION),
            forbidden_tokens=_as_token_map(data.get("forbidden_tokens")),
            grade_issue_keys=_as_str_list(data.get("grade_issue_keys")),
            grade_returncode_keys=_as_str_list(data.get("grade_returncode_keys")),
            success_threshold_hard=_as_float(
                data.get("success_threshold_hard"),
                _DEFAULT_SUCCESS_THRESHOLD_HARD,
            ),
            max_examples=_as_int(data.get("max_examples"), _DEFAULT_MAX_EXAMPLES),
        )

    @staticmethod
    def from_path(path: Path) -> Rubric:
        if not path.is_file():
            raise ConfigError(
                f"rubric not found: {path}",
                code="rubric_missing",
                context={"path": str(path)},
            )
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(
                f"rubric is not valid JSON: {path}",
                code="rubric_json",
                context={"path": str(path), "error": str(exc)},
            ) from exc
        match raw:
            case Mapping() as m:
                return Rubric.from_mapping(cast(Mapping[str, object], m))
            case _:
                raise ConfigError(
                    f"rubric root must be an object: {path}",
                    code="rubric_shape",
                    context={"path": str(path)},
                )

    def to_mapping(self) -> RubricDict:
        return {
            "name": self.name,
            "description": self.description,
            "forbidden_tokens": dict(self.forbidden_tokens),
            "grade_issue_keys": list(self.grade_issue_keys),
            "grade_returncode_keys": list(self.grade_returncode_keys),
            "success_threshold_hard": self.success_threshold_hard,
            "max_examples": self.max_examples,
        }

    def bucket_for_token(self, token: str) -> str | None:
        return self.forbidden_tokens.get(token)


__all__ = ["Rubric", "RubricDict"]
