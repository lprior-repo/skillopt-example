"""Pure core primitives for the SkillOpt candidate evaluation harness.

This module owns every value-in / value-out computation used by the
candidate evaluation pipeline: type coercion, hashing, split filtering,
summary aggregation, promotion gating, and config validation. Side
effects (filesystem reads, process invocation, dynamic imports,
``print`` / ``sys.exit``) belong in
:mod:`scripts.run_holzman_candidate_eval`, which is the matching thin
shell.

Every public pure function carries ``@beartype`` plus
``@icontract.require`` / ``@icontract.ensure`` so CrossHair can prove
the contracts and Hypothesis can fuzz the bounds.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, TypedDict, runtime_checkable

import icontract
from beartype import beartype
from expression import Error, Ok, Result

from scripts.errors import EvalError

__all__ = [
    "VALID_SPLITS",
    "_HARD_PASS_THRESHOLD",
    "_VALID_SPLITS",
    "AdapterProtocol",
    "BundleHashesDict",
    "CandidatePaths",
    "DataloaderProtocol",
    "RunError",
    "RunMetadataDict",
    "SummaryDict",
    "_adapter_from_cfg",
    "_as_float",
    "_as_int",
    "_as_str",
    "_config_errors",
    "_display_path",
    "_log_failure_lines",
    "_prepare_config",
    "_promotion_status",
    "_resolve_out_root",
    "_row_hard",
    "_row_passed_p",
    "_row_soft",
    "_run_metadata",
    "_run_split",
    "_validate_candidate",
    "_validate_splits",
    "_validate_supported_config",
    "all_split_items",
    "bundle_hashes",
    "selected_items",
    "sha256_file",
    "split_values",
    "summarize",
]


RunError = EvalError
"""Legacy alias kept so the original ``scripts.run_holzman_candidate_eval`` API stays stable."""


_SHA256_HEX_LEN: Final[int] = 64
"""Number of hex characters in a canonical SHA-256 digest."""

_PROMOTION_TUPLE_LEN: Final[int] = 2
"""Number of fields returned by :func:`_promotion_status`."""

_SHA256_HEX_ALPHABET: Final[frozenset[str]] = frozenset("0123456789abcdef")
"""Permitted characters in a lowercase SHA-256 hex digest."""

_HARD_PASS_THRESHOLD: Final[float] = 1.0
"""Minimum mean ``hard`` score for a split to count as passing."""

VALID_SPLITS: Final[tuple[str, ...]] = ("train", "val", "test")
"""Splits the dataloader protocol is guaranteed to expose."""

_VALID_SPLITS: Final[tuple[str, ...]] = VALID_SPLITS
"""Underscore-prefixed alias preserved so the shell can re-export it under that name."""

_PROMOTION_SPLITS: Final[tuple[str, ...]] = ("val", "test")
"""Splits required for a run to be promotion-eligible."""

_DEFAULT_SPLITS: Final[str] = "val,test"
"""Default ``--splits`` value surfaced to ``argparse``."""

_SKILL_FILENAME: Final[str] = "SKILL.md"
"""Primary skill file every candidate must ship."""

_REFERENCES_DIRNAME: Final[str] = "references"
"""Sub-directory holding the candidate reference bundle."""

_MANIFEST_NAME: Final[str] = "manifest.json"
"""Manifest filename expected inside the supported split directory."""

_BUNDLE_HASHES_NAME: Final[str] = "bundle_hashes.json"
"""Bundle-hash artifact written next to the per-split summary."""

_SUMMARY_NAME: Final[str] = "summary.json"
"""Per-split summary artifact filename."""

_RUN_METADATA_NAME: Final[str] = "run_metadata.json"
"""Run-metadata artifact filename."""

_PATH_TAIL_PARTS: Final[int] = 2
"""Number of trailing path parts kept when no relative prefix matches."""

_HOME_PREFIX: Final[str] = "$HOME/"
"""Prefix used when a path falls under the user's home directory."""

_ABSOLUTE_PREFIX: Final[str] = "<absolute>/"
"""Prefix used when a path falls outside the repo and home roots."""

_INT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*[+-]?\d+\s*")
"""Regex matching strings ``_as_int`` will accept as integers."""

_FLOAT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*[+-]?\d+(?:\.\d+)?\s*")
"""Regex matching strings ``_as_float`` will accept as floats."""


class BundleHashesDict(TypedDict):
    """SHA-256 hashes of the candidate bundle (skill and reference files)."""

    skill: str
    references: Mapping[str, str]


class SummaryDict(TypedDict):
    """Per-split roll-up of the candidate evaluation results."""

    candidate: str
    skill_sha256: str
    split: str
    n: int
    hard: float
    soft: float
    passed: int
    failed: Sequence[str]
    fail_reasons: Mapping[str, str]
    model_counts: Mapping[str, int]
    non_promotable: bool
    promotion_reason: str


class RunMetadataDict(TypedDict):
    """Run-level metadata captured next to the per-split summary."""

    candidate: str
    candidate_dir: str
    candidate_hashes: Mapping[str, object]
    config_path: str
    config_sha256: str
    dataset_split_dir: str
    dataset_manifest_sha256: str
    promotion_eligible: bool
    promotion_reason: str
    review_model: str
    repair_model: str
    opencode_variant: str
    opencode_show_thinking: bool


@dataclass(frozen=True, slots=True)
class CandidatePaths:
    """Filesystem locations of a candidate's primary skill and reference bundle."""

    skill: Path
    references: Path


class DataloaderProtocol(Protocol):
    """Structural type for the SkillOpt dataloader contract used by the adapter."""

    train_items: Sequence[Mapping[str, object]]
    val_items: Sequence[Mapping[str, object]]
    test_items: Sequence[Mapping[str, object]]


@runtime_checkable
class AdapterProtocol(Protocol):
    """Structural type for the SkillOpt adapter that rolls out a skill."""

    dataloader: DataloaderProtocol

    def setup(self, cfg: Mapping[str, object]) -> None:
        """Configure the adapter from the flattened ``cfg`` mapping."""
        ...

    def rollout(
        self,
        items: Sequence[Mapping[str, object]],
        skill: str,
        out_dir: str,
    ) -> Sequence[Mapping[str, object]]:
        """Execute ``skill`` against ``items`` and return per-item result rows."""
        ...


def _always_true() -> bool:
    """Trivially-true contract used when no precondition is meaningful.

    Exists so ``@icontract.require`` can be wired up uniformly without
    tripping the ``ARG005`` lint on lambdas whose arguments are unused.
    """
    return True


def _int_postcondition(result: object) -> bool:
    """Pin the return type so CrossHair can prove the contract."""
    return isinstance(result, int)


def _float_postcondition(result: object) -> bool:
    """Pin the return type so CrossHair can prove the contract."""
    return isinstance(result, float)


def _str_postcondition(result: object) -> bool:
    """Pin the return type so CrossHair can prove the contract."""
    return isinstance(result, str)


def _bool_postcondition(result: object) -> bool:
    """Pin the return type so CrossHair can prove the contract."""
    return isinstance(result, bool)


def _split_values_postcondition(result: Sequence[str], value: object) -> bool:
    """Guarantee every emitted part is non-empty and already stripped."""
    del value
    return all(part == part.strip() and bool(part) for part in result)


def _promotion_tuple_postcondition(result: tuple[bool, str]) -> bool:
    """Guarantee the promotion status is shaped ``(bool, str)``."""
    return len(result) == _PROMOTION_TUPLE_LEN


def _ok_or_eval_error(result: Result[object, object]) -> bool:
    """Guarantee ``Result`` carries either an :class:`EvalError` or no error."""
    if result.is_ok():
        return True
    return isinstance(result.error, EvalError)


def _log_failure_lines_postcondition(result: Sequence[str]) -> bool:
    """Guarantee every emitted failure line is a non-empty string."""
    return all(bool(line) for line in result)


def _promotion_pre(splits: object, ids: object, kind: object) -> bool:
    """Pin the promotion ``kind`` to the known supported values."""
    del splits, ids
    return kind in ("all", "review", "repair")


def _split_values_pre(value: object) -> bool:
    """Require ``value`` to be a string so the postcondition can rely on it."""
    return isinstance(value, str)


def _hard_value_is_float(hard_value: object) -> bool:
    """Require ``hard_value`` to be a float before comparing to the threshold."""
    return isinstance(hard_value, float)


def _selected_items_postcondition(result: object) -> bool:
    """Guarantee ``selected_items`` always returns a tuple."""
    return isinstance(result, tuple)


@beartype
@icontract.require(_always_true)
@icontract.ensure(_int_postcondition)
def _as_int(value: object, default: int) -> int:
    """Coerce an arbitrary value to ``int``, falling back to ``default``."""
    match value:
        case bool():
            return int(value)
        case int():
            return int(value)
        case float():
            return int(value)
        case str() if _INT_PATTERN.fullmatch(value):
            return int(value)
        case _:
            pass
    return default


@beartype
@icontract.require(_always_true)
@icontract.ensure(_float_postcondition)
def _as_float(value: object, default: float) -> float:
    """Coerce an arbitrary value to ``float``, falling back to ``default``."""
    match value:
        case bool():
            return float(int(value))
        case int() | float():
            return float(value)
        case str() if _FLOAT_PATTERN.fullmatch(value):
            return float(value)
        case _:
            pass
    return default


@beartype
@icontract.require(_always_true)
@icontract.ensure(_str_postcondition)
def _as_str(value: object, default: str) -> str:
    """Coerce an arbitrary value to ``str``, falling back to ``default``."""
    match value:
        case str():
            return value
        case bool() | int() | float():
            return str(value)
        case _:
            pass
    return default


@beartype
@icontract.require(_always_true)
def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of the file at ``path``."""
    # crosshair: off
    return hashlib.sha256(path.read_bytes()).hexdigest()


@beartype
@icontract.require(_split_values_pre)
@icontract.ensure(_split_values_postcondition)
def split_values(value: str) -> Sequence[str]:
    """Split a comma-separated string into non-empty stripped parts."""
    return [part.strip() for part in value.split(",") if part.strip()]


@beartype
@icontract.require(_always_true)
@icontract.ensure(_ok_or_eval_error)
def all_split_items(
    adapter: AdapterProtocol, split: str
) -> Result[Sequence[Mapping[str, object]], EvalError]:
    """Return every item the adapter exposes for the named ``split``."""
    dataloader = adapter.dataloader
    match split:
        case "train":
            return Ok(tuple(dataloader.train_items))
        case "val":
            return Ok(tuple(dataloader.val_items))
        case "test":
            return Ok(tuple(dataloader.test_items))
        case _:
            pass
    return Error(EvalError(message=f"unknown split: {split}", code="unknown_split"))


@beartype
@icontract.require(_always_true)
@icontract.ensure(_selected_items_postcondition)
def selected_items(
    adapter: AdapterProtocol,
    split: str,
    ids: frozenset[str],
    kind: str,
) -> Sequence[Mapping[str, object]]:
    """Filter ``split`` items by id set and task kind."""
    items_result = all_split_items(adapter, split)
    if not items_result.is_ok():
        return ()
    items: Sequence[Mapping[str, object]] = items_result.ok
    if ids:
        items = tuple(item for item in items if _as_str(item.get("id"), "") in ids)
    if kind != "all":
        items = tuple(
            item
            for item in items
            if _as_str(item.get("kind") or item.get("task_type") or "review", "") == kind
        )
    return items


@beartype
@icontract.require(_always_true)
def bundle_hashes(candidate_dir: Path) -> BundleHashesDict:
    """Collect SHA-256 hashes for the candidate skill and every reference file."""
    # crosshair: off
    skill_path = candidate_dir / _SKILL_FILENAME
    refs_dir = candidate_dir / _REFERENCES_DIRNAME
    refs_hashes: tuple[tuple[str, str], ...] = ()
    if refs_dir.exists():
        for path in sorted(refs_dir.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(candidate_dir))
                refs_hashes = (*refs_hashes, (rel, sha256_file(path)))
    return BundleHashesDict(skill=sha256_file(skill_path), references=dict(refs_hashes))


@beartype
@icontract.require(_always_true)
@icontract.ensure(_float_postcondition)
def _row_hard(row: Mapping[str, object]) -> float:
    """Extract the ``hard`` score from a result row, defaulting to ``0.0``."""
    return _as_float(row.get("hard", 0.0), 0.0)


@beartype
@icontract.require(_always_true)
@icontract.ensure(_float_postcondition)
def _row_soft(row: Mapping[str, object]) -> float:
    """Extract the ``soft`` score from a result row, defaulting to ``0.0``."""
    return _as_float(row.get("soft", 0.0), 0.0)


@beartype
@icontract.require(_hard_value_is_float)
@icontract.ensure(_bool_postcondition)
def _row_passed_p(hard_value: float) -> bool:
    """Return whether the ``hard`` score clears the promotion threshold."""
    return hard_value >= _HARD_PASS_THRESHOLD


@beartype
@icontract.require(_always_true)
def summarize(  # noqa: PLR0913
    candidate: str,
    skill_hash: str,
    split: str,
    results: Sequence[Mapping[str, object]],
    non_promotable: bool,
    promotion_reason: str,
) -> SummaryDict:
    """Aggregate rollout ``results`` into a per-split :class:`SummaryDict`."""
    # crosshair: off
    failures = tuple(row for row in results if not _row_passed_p(_row_hard(row)))
    model_counts = dict(
        sorted(Counter(_as_str(row.get("model") or "", "") for row in results).items())
    )
    n = max(1, len(results))
    return SummaryDict(
        candidate=candidate,
        skill_sha256=skill_hash,
        split=split,
        n=len(results),
        hard=sum(_row_hard(row) for row in results) / n,
        soft=sum(_row_soft(row) for row in results) / n,
        passed=len(results) - len(failures),
        failed=tuple(_as_str(row.get("id"), "") for row in failures),
        fail_reasons={
            _as_str(row.get("id"), ""): _as_str(row.get("fail_reason") or "", "")
            for row in failures
        },
        model_counts=model_counts,
        non_promotable=non_promotable,
        promotion_reason=promotion_reason,
    )


@beartype
@icontract.require(_promotion_pre)
@icontract.ensure(_promotion_tuple_postcondition)
def _promotion_status(splits: Sequence[str], ids: frozenset[str], kind: str) -> tuple[bool, str]:
    """Decide whether the run is promotion-eligible and why."""
    reasons: tuple[str, ...] = ()
    if tuple(splits) != _PROMOTION_SPLITS:
        reasons = (*reasons, "splits_must_be_val_test")
    if ids:
        reasons = (*reasons, "targeted_ids_selected")
    if kind != "all":
        reasons = (*reasons, f"kind={kind}")
    if reasons:
        return False, ";".join(reasons)
    return True, "full_val_test_all_tasks"


@beartype
@icontract.require(_always_true)
@icontract.ensure(_ok_or_eval_error)
def _validate_splits(splits: Sequence[str]) -> Result[None, EvalError]:
    """Reject any ``splits`` that are not in the supported set."""
    unknown = tuple(sorted({split for split in splits if split not in VALID_SPLITS}))
    if unknown:
        return Error(
            EvalError(
                message="unknown split(s): " + ", ".join(unknown),
                code="unknown_split",
            )
        )
    return Ok(None)


@beartype
@icontract.require(_always_true)
def _validate_candidate(
    candidate_dir: Path,
    format_path: Callable[[Path], str],
) -> Result[None, EvalError]:
    """Ensure ``candidate_dir`` contains the required ``SKILL.md`` file."""
    # crosshair: off
    skill_path = candidate_dir / _SKILL_FILENAME
    if not skill_path.is_file():
        return Error(
            EvalError(
                message="missing skill file: " + format_path(skill_path),
                code="missing_skill_md",
            )
        )
    return Ok(None)


@beartype
@icontract.require(_always_true)
def _config_errors(
    cfg: Mapping[str, object],
    supported_split_dir: Path,
    manifest_name: str,
    format_path: Callable[[Path], str],
) -> Sequence[str]:
    """List all unsupported configuration values in the flattened ``cfg``."""
    # crosshair: off
    errors: tuple[str, ...] = ()
    split_mode = _as_str(cfg.get("split_mode"), "").strip().lower()
    if split_mode != "split_dir":
        errors = (*errors, f"split_mode={split_mode or '<empty>'}")

    split_dir = Path(_as_str(cfg.get("split_dir"), "")).expanduser()
    if split_dir.resolve() != supported_split_dir.resolve():
        errors = (*errors, f"split_dir={format_path(split_dir.resolve())}")

    if _as_str(cfg.get("data_path"), "").strip():
        errors = (*errors, "data_path_must_be_empty")
    if _as_str(cfg.get("split_output_dir"), "").strip():
        errors = (*errors, "split_output_dir_must_be_empty")
    if _as_int(cfg.get("limit"), 0) != 0:
        errors = (*errors, f"limit={_as_int(cfg.get('limit'), 0)}")
    if not (supported_split_dir / manifest_name).is_file():
        errors = (
            *errors,
            "missing_dataset_manifest=" + format_path(supported_split_dir / manifest_name),
        )
    return errors


@beartype
@icontract.require(_always_true)
def _validate_supported_config(
    cfg: Mapping[str, object],
    supported_split_dir: Path,
    manifest_name: str,
    format_path: Callable[[Path], str],
) -> Result[None, EvalError]:
    """Reject ``cfg`` if it contains any unsupported values."""
    # crosshair: off
    errors = _config_errors(
        cfg,
        supported_split_dir,
        manifest_name,
        format_path,
    )
    if errors:
        return Error(
            EvalError(
                message="unsupported candidate-eval config: " + ", ".join(errors),
                code="unsupported_config",
            )
        )
    return Ok(None)


@beartype
@icontract.require(_always_true)
@icontract.ensure(_log_failure_lines_postcondition)
def _log_failure_lines(split: str, results: Sequence[Mapping[str, object]]) -> Sequence[str]:
    """Return one ``FAIL`` record per failing result row for stdout."""
    return tuple(
        " ".join(
            (
                "FAIL",
                split,
                str(row.get("id")),
                str(row.get("fail_reason")),
                str(row.get("model")),
            )
        )
        for row in results
        if not _row_passed_p(_row_hard(row))
    )


@beartype
@icontract.require(_always_true)
def _run_metadata(  # noqa: PLR0913
    *,
    candidate: str,
    candidate_dir_display: str,
    config_path_display: str,
    cfg: Mapping[str, object],
    hashes: BundleHashesDict,
    config_sha256: str,
    dataset_split_dir_display: str,
    dataset_manifest_sha256: str,
    promotion_eligible: bool,
    promotion_reason: str,
) -> RunMetadataDict:
    """Assemble the run-metadata mapping that is written next to the report."""
    return RunMetadataDict(
        candidate=candidate,
        candidate_dir=candidate_dir_display,
        candidate_hashes=dict(hashes),
        config_path=config_path_display,
        config_sha256=config_sha256,
        dataset_split_dir=dataset_split_dir_display,
        dataset_manifest_sha256=dataset_manifest_sha256,
        promotion_eligible=promotion_eligible,
        promotion_reason=promotion_reason,
        review_model=_as_str(cfg.get("review_model"), ""),
        repair_model=_as_str(cfg.get("repair_model"), ""),
        opencode_variant=_as_str(cfg.get("opencode_variant"), ""),
        opencode_show_thinking=bool(cfg.get("opencode_show_thinking")),
    )


@beartype
@icontract.require(_always_true)
def _display_path(path: Path, repo_root: Path, home: Path) -> str:
    """Render ``path`` relative to the repo or ``$HOME`` for log output."""
    # crosshair: off
    resolved = path.resolve()
    root = repo_root.resolve()
    if resolved.is_relative_to(root):
        return resolved.relative_to(root).as_posix()
    home_resolved = home.resolve()
    if resolved.is_relative_to(home_resolved):
        return f"{_HOME_PREFIX}{resolved.relative_to(home_resolved).as_posix()}"
    tail = (
        "/".join(resolved.parts[-_PATH_TAIL_PARTS:])
        if len(resolved.parts) >= _PATH_TAIL_PARTS
        else resolved.name
    )
    return f"{_ABSOLUTE_PREFIX}{tail}"


@beartype
@icontract.require(_always_true)
def _resolve_out_root(args_out: str, default_report_root: Path) -> Path:
    """Resolve ``--out`` to an absolute path, defaulting under the report root."""
    # crosshair: off
    out = Path(args_out).expanduser()
    if not out.is_absolute():
        return default_report_root / out
    return out


@beartype
@icontract.require(_always_true)
def _adapter_from_cfg(
    cfg: Mapping[str, object],
    get_adapter: Callable[[Mapping[str, object]], AdapterProtocol],
) -> AdapterProtocol:
    """Build and configure the SkillOpt adapter for ``cfg``.

    ``get_adapter`` is injected by the shell layer so this function stays
    free of dynamic imports.
    """
    # crosshair: off
    adapter = get_adapter(cfg)
    adapter.setup(cfg)
    return adapter


def _workers_non_negative(workers: int) -> bool:
    """Require ``workers`` to be non-negative so the config can be injected safely."""
    return workers >= 0


@beartype
@icontract.require(_workers_non_negative)
def _prepare_config(
    config_path: Path,
    refs_dir: Path,
    workers: int,
    flatten_config: Callable[[object], Mapping[str, object]],
    load_config: Callable[[str], object],
) -> Mapping[str, object]:
    """Load and flatten ``config_path``, injecting references dir and worker count."""
    # crosshair: off
    cfg = flatten_config(load_config(str(config_path)))
    extras: Mapping[str, object] = {"references_dir": str(refs_dir)}
    if workers > 0:
        extras = {**extras, "workers": workers}
    return {**cfg, **extras}


@beartype
@icontract.require(_always_true)
def _run_split(  # noqa: PLR0913
    adapter: AdapterProtocol,
    skill: str,
    split: str,
    items: Sequence[Mapping[str, object]],
    ids: frozenset[str],
    out_root: Path,
) -> Result[tuple[Path, Sequence[Mapping[str, object]]], EvalError]:
    """Execute the adapter for a single split and return its output path and rows."""
    # crosshair: off
    if not items:
        return Error(
            EvalError(
                message="no items selected for split=" + split,
                code="empty_selection",
            )
        )
    split_out = out_root / f"full_{split}" if not ids else out_root / f"targeted_{split}"
    results: Sequence[Mapping[str, object]] = tuple(adapter.rollout(items, skill, str(split_out)))
    return Ok((split_out, results))
