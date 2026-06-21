from __future__ import annotations

from typing import TYPE_CHECKING, Final

from .budget import Budget, BudgetConfig, BudgetState, PlateauDetector
from .ci_runner import main as ci_main
from .diff_report import FailureBucket, FailureDiff, categorize, diff_runs, render_markdown
from .diff_report import main as diff_main
from .errors import (
    BudgetExceeded,
    ConfigError,
    DiffError,
    Err,
    EvalError,
    LeaderboardError,
    MutatorError,
    Ok,
    PlateauReached,
    ProviderError,
    Result,
    TrainError,
)
from .eval_bridge import EvalResult, run_eval
from .leaderboard import Leaderboard, LeaderboardEntry, best_entry
from .leaderboard import main as lb_main
from .mutator import DEFAULT_PROMPT, Mutator, MutatorMeta, hash_overlay, propose, propose_from_skill
from .providers import (
    MockProvider,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ScriptedTurn,
    Usage,
    estimate_tokens,
    extract_json,
    load_provider,
    make_json_response,
    now_ms,
)
from .rubric import Rubric, RubricDict
from .self_critique import (
    CritiqueBlock,
    build_critique,
    inject_critique,
    top_failure_modes,
)
from .skill import REQUIRED_FILES, Skill
from .skill_train import SkillDrivenConfig, SkillDrivenLoop
from .skill_train import main as skill_train_main
from .train_loop import LoopConfig, LoopState, SkillOptLoop
from .train_loop import main as train_main

if TYPE_CHECKING:
    from .providers import AnthropicProvider, OpenAIProvider, OpencodeProvider

_LAZY_PROVIDER_NAMES: Final[dict[str, str]] = {
    "AnthropicProvider": ".providers",
    "OpenAIProvider": ".providers",
    "OpencodeProvider": ".providers",
}

__all__ = [
    "DEFAULT_PROMPT",
    "REQUIRED_FILES",
    "AnthropicProvider",
    "Budget",
    "BudgetConfig",
    "BudgetExceeded",
    "BudgetState",
    "ConfigError",
    "CritiqueBlock",
    "DiffError",
    "Err",
    "EvalError",
    "EvalResult",
    "FailureBucket",
    "FailureDiff",
    "Leaderboard",
    "LeaderboardEntry",
    "LeaderboardError",
    "LoopConfig",
    "LoopState",
    "MockProvider",
    "ModelProvider",
    "ModelRequest",
    "ModelResponse",
    "Mutator",
    "MutatorError",
    "MutatorMeta",
    "Ok",
    "OpenAIProvider",
    "OpencodeProvider",
    "PlateauDetector",
    "PlateauReached",
    "ProviderError",
    "Result",
    "Rubric",
    "RubricDict",
    "ScriptedTurn",
    "Skill",
    "SkillDrivenConfig",
    "SkillDrivenLoop",
    "SkillOptLoop",
    "TrainError",
    "Usage",
    "best_entry",
    "build_critique",
    "categorize",
    "ci_main",
    "diff_main",
    "diff_runs",
    "estimate_tokens",
    "extract_json",
    "hash_overlay",
    "inject_critique",
    "lb_main",
    "load_provider",
    "make_json_response",
    "now_ms",
    "propose",
    "propose_from_skill",
    "render_markdown",
    "run_eval",
    "skill_train_main",
    "top_failure_modes",
    "train_main",
]


def __getattr__(name: str) -> object:
    module_rel = _LAZY_PROVIDER_NAMES.get(name)
    if module_rel is not None:
        import importlib

        module = importlib.import_module(module_rel, __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals().keys(), *__all__})
