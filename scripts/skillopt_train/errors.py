from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, TypedDict, TypeVar, final


class TrainErrorDict(TypedDict):
    code: str
    message: str
    context: dict[str, str]


class TrainError(Exception):
    code: str = "train_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        context: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        match code:
            case str() as c:
                self.code = c
            case _:
                pass
        self.context: dict[str, str] = dict(context) if context else {}

    def to_dict(self) -> TrainErrorDict:
        return {"code": self.code, "message": str(self), "context": dict(self.context)}


class ConfigError(TrainError):
    code: str = "config_error"


class ProviderError(TrainError):
    code: str = "provider_error"


class BudgetExceeded(TrainError):
    code: str = "budget_exceeded"


class PlateauReached(TrainError):
    code: str = "plateau_reached"


class MutatorError(TrainError):
    code: str = "mutator_error"


class EvalError(TrainError):
    code: str = "eval_error"


class LeaderboardError(TrainError):
    code: str = "leaderboard_error"


class DiffError(TrainError):
    code: str = "diff_error"


TRAIN_ERROR_CODES: Final[frozenset[str]] = frozenset({
    "config_error",
    "provider_error",
    "budget_exceeded",
    "plateau_reached",
    "mutator_error",
    "eval_error",
    "leaderboard_error",
    "diff_error",
    "train_error",
})


_D = TypeVar("_D")


@final
@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T
    is_ok: bool = True
    is_err: bool = False

    def unwrap_or(self, default: T) -> T:
        return self.value


@final
@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E
    is_ok: bool = False
    is_err: bool = True

    def unwrap_or(self, default: _D) -> _D:
        return default


_T = TypeVar("_T")
_E = TypeVar("_E")
Result = Ok[_T] | Err[_E]