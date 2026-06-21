#!/usr/bin/env python3
"""Run SkillOpt candidate evaluations against the Holzman Rust dataset.

The shell validates the candidate directory, hashes the bundle, runs the
adapter over each requested split, and writes a per-split summary plus an
aggregate roll-up to the report directory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol, TypedDict, cast

from expression import Error, Ok, Result

if TYPE_CHECKING:
    from collections.abc import MutableMapping, MutableSequence


class _Dataloader(Protocol):
    """Structural type for the SkillOpt dataloader contract used by the adapter."""

    train_items: Sequence[Mapping[str, object]]
    val_items: Sequence[Mapping[str, object]]
    test_items: Sequence[Mapping[str, object]]


class _Adapter(Protocol):
    """Structural type for the SkillOpt adapter that rolls out a skill."""

    dataloader: _Dataloader

    def setup(self, cfg: Mapping[str, object]) -> None:
        """Configure the adapter from the flattened ``cfg`` mapping."""
        ...

    def rollout(
        self,
        items: Sequence[Mapping[str, object]],
        skill: str,
        _out_dir: str,
    ) -> Sequence[Mapping[str, object]]:
        """Execute ``skill`` against ``items`` and return per-item result rows."""
        ...


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


_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SKILLOPT_ROOT: Final[Path] = _ROOT / "vendor" / "SkillOpt"
_DEFAULT_CONFIG: Final[Path] = _SKILLOPT_ROOT / "configs" / "holzman_rust" / "aggressive.yaml"
_DEFAULT_CANDIDATE_DIR: Final[Path] = _ROOT / "candidates" / "holzman-rust-candidate-v13"
_DEFAULT_REPORT_ROOT: Final[Path] = _ROOT / "reports" / "holzman-rust"
_VALID_SPLITS: Final[tuple[str, ...]] = ("train", "val", "test")
_HARD_PASS_THRESHOLD: Final[float] = 1.0
_BUNDLE_HASHES_NAME: Final[str] = "bundle_hashes.json"
_SUMMARY_NAME: Final[str] = "summary.json"
_RUN_METADATA_NAME: Final[str] = "run_metadata.json"
_REFERENCES_DIRNAME: Final[str] = "references"
_SKILL_FILENAME: Final[str] = "SKILL.md"
_SUPPORTED_SPLIT_DIR: Final[Path] = _ROOT / "data" / "holzman_rust_aggressive"
_MANIFEST_NAME: Final[str] = "manifest.json"
_PROMOTION_SPLITS: Final[tuple[str, ...]] = ("val", "test")
_DEFAULT_SPLITS: Final[str] = "val,test"
_PATH_TAIL_PARTS: Final[int] = 2
_HOME_PREFIX: Final[str] = "$HOME/"
_ABSOLUTE_PREFIX: Final[str] = "<absolute>/"
_INT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*[+-]?\d+\s*")
_FLOAT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*[+-]?\d+(?:\.\d+)?\s*")


@dataclass(frozen=True, slots=True)
class CandidatePaths:
    """Filesystem locations of a candidate's primary skill and reference bundle."""

    skill: Path
    references: Path


class RunError(Exception):
    """Typed exception carrying a machine-readable ``code`` for the shell layer."""

    code: str

    def __init__(self, message: str, *, code: str = "run_error") -> None:
        """Store ``message`` alongside a structured ``code`` identifier."""
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:
        """Render the error as ``[code] message`` for log output."""
        return f"[{self.code}] {super().__str__()}"


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


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of the file at ``path``."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_values(  # nosemgrep: python.no-mutable-collection-annotations
    value: str,
) -> Sequence[str]:
    """Split a comma-separated string into non-empty stripped parts."""
    return [part.strip() for part in value.split(",") if part.strip()]


def all_split_items(
    adapter: _Adapter, split: str
) -> Result[Sequence[Mapping[str, object]], RunError]:
    """Return every item the adapter exposes for the named ``split``."""
    dataloader = adapter.dataloader
    match split:
        case "train":
            items: Sequence[Mapping[str, object]] = tuple(dataloader.train_items)
            return Ok(items)
        case "val":
            items = tuple(dataloader.val_items)
            return Ok(items)
        case "test":
            items = tuple(dataloader.test_items)
            return Ok(items)
        case _:
            pass
    return Error(RunError(f"unknown split: {split}", code="unknown_split"))


def selected_items(
    adapter: _Adapter,
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


def _sha256_relative(root: Path, path: Path) -> str:  # noqa: ARG001
    """Hash ``path`` (the ``root`` argument is reserved for future use)."""
    return sha256_file(path)


def bundle_hashes(candidate_dir: Path) -> BundleHashesDict:
    """Collect SHA-256 hashes for the candidate skill and every reference file."""
    skill_path = candidate_dir / _SKILL_FILENAME
    refs_dir = candidate_dir / _REFERENCES_DIRNAME
    refs_hashes: MutableMapping[str, str] = {}
    if refs_dir.exists():
        for path in sorted(refs_dir.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(candidate_dir))
                refs_hashes[rel] = _sha256_relative(candidate_dir, path)
    return BundleHashesDict(
        skill=sha256_file(skill_path),
        references=refs_hashes,
    )


def _row_hard(row: Mapping[str, object]) -> float:
    """Extract the ``hard`` score from a result row, defaulting to ``0.0``."""
    return _as_float(row.get("hard", 0.0), 0.0)


def _row_soft(row: Mapping[str, object]) -> float:
    """Extract the ``soft`` score from a result row, defaulting to ``0.0``."""
    return _as_float(row.get("soft", 0.0), 0.0)


def _row_passed_p(hard_value: float) -> bool:
    """Return whether the ``hard`` score clears the promotion threshold."""
    return hard_value >= _HARD_PASS_THRESHOLD


def summarize(  # noqa: PLR0913
    candidate: str,
    skill_hash: str,
    split: str,
    results: Sequence[Mapping[str, object]],
    non_promotable: bool,
    promotion_reason: str,
) -> SummaryDict:
    """Aggregate rollout ``results`` into a per-split :class:`SummaryDict`."""
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


def _resolve_out_root(args_out: str) -> Path:
    """Resolve ``--out`` to an absolute path, defaulting under the report root."""
    out = Path(args_out).expanduser()
    if not out.is_absolute():
        return _DEFAULT_REPORT_ROOT / out
    return out


def _display_path(path: Path) -> str:
    """Render ``path`` relative to the repo or ``$HOME`` for log output."""
    resolved = path.resolve()
    root = _ROOT.resolve()
    if resolved.is_relative_to(root):
        return resolved.relative_to(root).as_posix()
    home = Path.home().resolve()
    if resolved.is_relative_to(home):
        return f"{_HOME_PREFIX}{resolved.relative_to(home).as_posix()}"
    tail = (
        "/".join(resolved.parts[-_PATH_TAIL_PARTS:])
        if len(resolved.parts) >= _PATH_TAIL_PARTS
        else resolved.name
    )
    return f"{_ABSOLUTE_PREFIX}{tail}"


def _validate_candidate(candidate_dir: Path) -> Result[None, RunError]:
    """Ensure ``candidate_dir`` contains the required ``SKILL.md`` file."""
    skill_path = candidate_dir / _SKILL_FILENAME
    if not skill_path.is_file():
        return Error(
            RunError(
                "missing skill file: " + _display_path(skill_path),
                code="missing_skill_md",
            )
        )
    return Ok(None)


def _config_errors(cfg: Mapping[str, object]) -> Sequence[str]:
    """List all unsupported configuration values in the flattened ``cfg``."""
    errors: MutableSequence[str] = []
    split_mode = _as_str(cfg.get("split_mode"), "").strip().lower()
    if split_mode != "split_dir":
        errors.append(f"split_mode={split_mode or '<empty>'}")

    split_dir = Path(_as_str(cfg.get("split_dir"), "")).expanduser()
    if split_dir.resolve() != _SUPPORTED_SPLIT_DIR.resolve():
        errors.append(f"split_dir={_display_path(split_dir.resolve())}")

    if _as_str(cfg.get("data_path"), "").strip():
        errors.append("data_path_must_be_empty")
    if _as_str(cfg.get("split_output_dir"), "").strip():
        errors.append("split_output_dir_must_be_empty")
    if _as_int(cfg.get("limit"), 0) != 0:
        errors.append(f"limit={_as_int(cfg.get('limit'), 0)}")
    if not (_SUPPORTED_SPLIT_DIR / _MANIFEST_NAME).is_file():
        errors.append(
            "missing_dataset_manifest=" + _display_path(_SUPPORTED_SPLIT_DIR / _MANIFEST_NAME)
        )
    return tuple(errors)


def _validate_supported_config(cfg: Mapping[str, object]) -> Result[None, RunError]:
    """Reject ``cfg`` if it contains any unsupported values."""
    errors = _config_errors(cfg)
    if errors:
        return Error(
            RunError(
                "unsupported candidate-eval config: " + ", ".join(errors),
                code="unsupported_config",
            )
        )
    return Ok(None)


def _promotion_status(splits: Sequence[str], ids: frozenset[str], kind: str) -> tuple[bool, str]:
    """Decide whether the run is promotion-eligible and why."""
    reasons: MutableSequence[str] = []
    if tuple(splits) != _PROMOTION_SPLITS:
        reasons.append("splits_must_be_val_test")
    if ids:
        reasons.append("targeted_ids_selected")
    if kind != "all":
        reasons.append(f"kind={kind}")
    if reasons:
        return False, ";".join(reasons)
    return True, "full_val_test_all_tasks"


def _validate_splits(splits: Sequence[str]) -> Result[None, RunError]:
    """Reject any ``splits`` that are not in the supported set."""
    unknown = tuple(sorted({split for split in splits if split not in _VALID_SPLITS}))
    if unknown:
        return Error(RunError("unknown split(s): " + ", ".join(unknown), code="unknown_split"))
    return Ok(None)


def _run_metadata(  # noqa: PLR0913
    *,
    candidate: str,
    candidate_dir: Path,
    config_path: Path,
    cfg: Mapping[str, object],
    hashes: BundleHashesDict,
    promotion_eligible: bool,
    promotion_reason: str,
) -> Mapping[str, object]:
    """Assemble the run-metadata mapping that is written next to the report."""
    manifest_path = _SUPPORTED_SPLIT_DIR / _MANIFEST_NAME
    return {
        "candidate": candidate,
        "candidate_dir": _display_path(candidate_dir),
        "candidate_hashes": dict(hashes),
        "config_path": _display_path(config_path),
        "config_sha256": sha256_file(config_path),
        "dataset_split_dir": _display_path(_SUPPORTED_SPLIT_DIR),
        "dataset_manifest_sha256": sha256_file(manifest_path),
        "promotion_eligible": promotion_eligible,
        "promotion_reason": promotion_reason,
        "review_model": _as_str(cfg.get("review_model"), ""),
        "repair_model": _as_str(cfg.get("repair_model"), ""),
        "opencode_variant": _as_str(cfg.get("opencode_variant"), ""),
        "opencode_show_thinking": bool(cfg.get("opencode_show_thinking")),
    }


def _prepare_config(config_path: Path, refs_dir: Path, workers: int) -> Mapping[str, object]:
    """Load and flatten ``config_path``, injecting references dir and worker count."""
    sys.path.insert(0, str(_SKILLOPT_ROOT.resolve()))
    config_module = importlib.import_module("skillopt.config")
    flatten_config = config_module.flatten_config
    load_config = config_module.load_config

    cfg_raw: Mapping[str, object] = cast(
        Mapping[str, object], flatten_config(load_config(str(config_path)))
    )
    cfg_dict = cast("dict[str, object]", cfg_raw)
    cfg_dict["references_dir"] = str(refs_dir)
    if workers > 0:
        cfg_dict["workers"] = workers
    return cfg_dict


def _run_split(  # noqa: PLR0913
    adapter: _Adapter,
    skill: str,
    split: str,
    items: Sequence[Mapping[str, object]],
    ids: frozenset[str],
    out_root: Path,
) -> Result[tuple[Path, Sequence[Mapping[str, object]]], RunError]:
    """Execute the adapter for a single split and return its output path and rows."""
    if not items:
        return Error(RunError("no items selected for split=" + split, code="empty_selection"))
    split_out = out_root / f"full_{split}" if not ids else out_root / f"targeted_{split}"
    results: Sequence[Mapping[str, object]] = tuple(adapter.rollout(items, skill, str(split_out)))
    return Ok((split_out, results))


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


def _adapter_from_cfg(cfg: Mapping[str, object]) -> _Adapter:
    """Build and configure the SkillOpt adapter for ``cfg``."""
    from scripts.train import get_adapter  # type: ignore[import-untyped] # noqa: PLC0415

    adapter = cast(_Adapter, get_adapter(cast("dict[str, object]", cfg)))
    adapter.setup(cfg)
    return adapter


def main(argv: Sequence[str]) -> Result[int, RunError]:  # noqa: PLR0911, PLR0915
    """Validate the candidate, run every requested split, and write the report."""
    parser = argparse.ArgumentParser(
        description="Run current SkillOpt Holzman candidate evaluations"
    )
    _ = parser.add_argument("--candidate-dir", default=str(_DEFAULT_CANDIDATE_DIR))
    _ = parser.add_argument("--config", default=str(_DEFAULT_CONFIG))
    _ = parser.add_argument(
        "--out",
        required=True,
        help="Output directory under reports/holzman-rust unless absolute",
    )
    _ = parser.add_argument(
        "--splits", default=_DEFAULT_SPLITS, help="Comma-separated train,val,test"
    )
    _ = parser.add_argument(
        "--ids", default="", help="Comma-separated task ids for targeted reruns"
    )
    _ = parser.add_argument("--kind", choices=["all", "review", "repair"], default="all")
    _ = parser.add_argument("--candidate-name", default="", help="Label stored in summaries")
    _ = parser.add_argument("--workers", type=int, default=0, help="Override env.workers")
    args = parser.parse_args(argv)

    candidate_dir = Path(args.candidate_dir).expanduser().resolve()
    validate_candidate_result = _validate_candidate(candidate_dir)
    if not validate_candidate_result.is_ok():
        return Error(validate_candidate_result.error)
    skill_path = candidate_dir / _SKILL_FILENAME
    refs_dir = candidate_dir / _REFERENCES_DIRNAME
    out_root = _resolve_out_root(args.out)
    out_root.mkdir(parents=True, exist_ok=True)  # nosemgrep: python.no-file-writes

    config_path = Path(args.config).expanduser().resolve()
    cfg = _prepare_config(config_path, refs_dir, args.workers)
    validate_config_result = _validate_supported_config(cfg)
    if not validate_config_result.is_ok():
        return Error(validate_config_result.error)
    adapter = _adapter_from_cfg(cfg)
    skill = skill_path.read_text(encoding="utf-8")
    hashes = bundle_hashes(candidate_dir)
    candidate = args.candidate_name or candidate_dir.name
    ids = frozenset(split_values(args.ids))
    splits = tuple(split_values(args.splits))
    validate_splits_result = _validate_splits(splits)
    if not validate_splits_result.is_ok():
        return Error(validate_splits_result.error)
    promotion_eligible, promotion_reason = _promotion_status(splits, ids, args.kind)
    all_summaries: MutableSequence[SummaryDict] = []

    metadata = _run_metadata(
        candidate=candidate,
        candidate_dir=candidate_dir,
        config_path=config_path,
        cfg=cfg,
        hashes=hashes,
        promotion_eligible=promotion_eligible,
        promotion_reason=promotion_reason,
    )

    _ = sys.stdout.write(
        json.dumps(
            {"out": _display_path(out_root), "run_metadata": metadata},
            indent=2,
        )
        + "\n"
    )
    _ = sys.stdout.flush()

    _ = (out_root / _BUNDLE_HASHES_NAME).write_text(  # nosemgrep: python.no-file-writes
        json.dumps(dict(hashes), indent=2) + "\n", encoding="utf-8"
    )
    _ = (out_root / _RUN_METADATA_NAME).write_text(  # nosemgrep: python.no-file-writes
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    for split in splits:
        items = selected_items(adapter, split, ids, args.kind)
        split_result = _run_split(adapter, skill, split, items, ids, out_root)
        if not split_result.is_ok():
            return Error(split_result.error)
        split_out, results = split_result.ok

        summary = summarize(
            candidate,
            str(hashes["skill"]),
            split,
            results,
            not promotion_eligible,
            promotion_reason,
        )
        _ = (split_out / _SUMMARY_NAME).write_text(  # nosemgrep: python.no-file-writes
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        all_summaries.append(summary)
        _ = sys.stdout.write(json.dumps(summary, indent=2) + "\n")
        _ = sys.stdout.flush()
        for line in _log_failure_lines(split, results):
            _ = sys.stdout.write(line + "\n")
        _ = sys.stdout.flush()

    _ = (out_root / _SUMMARY_NAME).write_text(  # nosemgrep: python.no-file-writes
        json.dumps(all_summaries, indent=2) + "\n", encoding="utf-8"
    )
    if not promotion_eligible:
        return Ok(2)
    if any(summary["hard"] < _HARD_PASS_THRESHOLD for summary in all_summaries):
        return Ok(1)
    return Ok(0)


if __name__ == "__main__":
    result = main(tuple(sys.argv[1:]))
    if result.is_ok():
        sys.exit(result.ok)
    else:
        sys.exit(1)
