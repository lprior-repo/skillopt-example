#!/usr/bin/env python3
"""Run SkillOpt candidate evaluations against the Holzman Rust dataset.

Thin shell: every value-in / value-out computation lives in
:mod:`scripts.eval_core`. This module only wires the CLI, reads /
writes files, dispatches to the SkillOpt adapter, and maps the
resulting ``Result`` onto an exit code.
"""

# pyright: reportPrivateUsage=false
from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

from expression import Error, Ok, Result

from scripts.errors import EvalError
from scripts.eval_core import (
    _BUNDLE_HASHES_NAME,
    _HARD_PASS_THRESHOLD,
    _MANIFEST_NAME,
    _REFERENCES_DIRNAME,
    _RUN_METADATA_NAME,
    _SKILL_FILENAME,
    _SUMMARY_NAME,
    AdapterProtocol,
    BundleHashesDict,
    CandidatePaths,
    SummaryDict,
    _adapter_from_cfg,
    _as_float,
    _as_int,
    _as_str,
    _display_path,
    _log_failure_lines,
    _prepare_config,
    _promotion_status,
    _resolve_out_root,
    _run_metadata,
    _run_split,
    _validate_candidate,
    _validate_splits,
    _validate_supported_config,
    all_split_items,
    bundle_hashes,
    selected_items,
    sha256_file,
    split_values,
    summarize,
)
from scripts.eval_core import (
    VALID_SPLITS as _VALID_SPLITS,
)

__all__ = [
    "_HARD_PASS_THRESHOLD",
    "_VALID_SPLITS",
    "AdapterProtocol",
    "BundleHashesDict",
    "CandidatePaths",
    "RunError",
    "SummaryDict",
    "_as_float",
    "_as_int",
    "_as_str",
    "_promotion_status",
    "all_split_items",
    "bundle_hashes",
    "sha256_file",
    "split_values",
]


def RunError(message: str, *, code: str = "run_error") -> EvalError:  # noqa: N802
    """Backward-compatible factory mirroring the original ``RunError(message, code=...)`` API.

    Returns an :class:`EvalError` instance so existing tests that construct
    errors positionally keep working without caring about the canonical
    ``EvalError(code, message)`` field order.
    """
    return EvalError(code=code, message=message)


if TYPE_CHECKING:
    pass


_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SKILLOPT_ROOT: Final[Path] = _ROOT / "vendor" / "SkillOpt"
_DEFAULT_CONFIG: Final[Path] = _SKILLOPT_ROOT / "configs" / "holzman_rust" / "aggressive.yaml"
_DEFAULT_CANDIDATE_DIR: Final[Path] = _ROOT / "candidates" / "holzman-rust-candidate-v13"
_DEFAULT_REPORT_ROOT: Final[Path] = _ROOT / "reports" / "holzman-rust"
_SUPPORTED_SPLIT_DIR: Final[Path] = _ROOT / "data" / "holzman_rust_aggressive"
_DEFAULT_SPLITS: Final[str] = "val,test"
_PROMOTION_SPLITS: Final[tuple[str, ...]] = ("val", "test")


def _shell_get_adapter(cfg: Mapping[str, object]) -> AdapterProtocol:
    """Dynamic-import the SkillOpt adapter factory at the shell layer.

    The cast lives here so :mod:`scripts.eval_core` stays free of
    ``importlib`` and runtime type-coercion.
    """
    from scripts.train import get_adapter  # type: ignore[import-untyped]  # noqa: PLC0415

    raw = cast("dict[str, object]", cfg)
    return cast(AdapterProtocol, get_adapter(raw))


def _shell_load_config(path_str: str) -> object:
    """Dynamic-import the SkillOpt config loaders at the shell layer."""
    sys.path.insert(0, str(_SKILLOPT_ROOT.resolve()))
    return importlib.import_module("skillopt.config").load_config(path_str)


def _shell_flatten_config(raw: object) -> Mapping[str, object]:
    """Flatten the SkillOpt config via its dedicated helper."""
    config_module = importlib.import_module("skillopt.config")
    return cast("Mapping[str, object]", config_module.flatten_config(raw))


def _build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for the eval shell."""
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
        "--splits",
        default=_DEFAULT_SPLITS,
        help="Comma-separated train,val,test",
    )
    _ = parser.add_argument(
        "--ids",
        default="",
        help="Comma-separated task ids for targeted reruns",
    )
    _ = parser.add_argument(
        "--kind",
        choices=["all", "review", "repair"],
        default="all",
    )
    _ = parser.add_argument(
        "--candidate-name",
        default="",
        help="Label stored in summaries",
    )
    _ = parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Override env.workers",
    )
    return parser


def _format_path(path: Path) -> str:
    """Render ``path`` for log output using the repo and home roots."""
    return _display_path(path, _ROOT.resolve(), Path.home())


def _validate_cli(args: argparse.Namespace) -> Result[None, EvalError]:
    """Pre-flight checks that can run before any IO happens."""
    if args.kind not in ("all", "review", "repair"):
        return Error(EvalError(message=f"unknown kind: {args.kind}", code="unknown_kind"))
    return Ok(None)


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    """Resolve the three filesystem roots used by the eval run."""
    candidate_dir = Path(args.candidate_dir).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()
    out_root = _resolve_out_root(args.out, _DEFAULT_REPORT_ROOT)
    return candidate_dir, config_path, out_root


def _ensure_out_root(out_root: Path) -> None:
    """Create the output directory, idempotent if it already exists."""
    out_root.mkdir(parents=True, exist_ok=True)  # nosemgrep: python.no-file-writes


def _load_flat_config(config_path: Path, refs_dir: Path, workers: int) -> Mapping[str, object]:
    """Inject runtime overrides into the SkillOpt config mapping."""
    return _prepare_config(
        config_path,
        refs_dir,
        workers,
        _shell_flatten_config,
        _shell_load_config,
    )


def _emit_metadata(metadata: Mapping[str, object], out_root: Path) -> None:
    """Print the run metadata and persist both bundle and metadata files."""
    _ = sys.stdout.write(
        json.dumps({"out": _format_path(out_root), "run_metadata": metadata}, indent=2) + "\n"
    )
    _ = sys.stdout.flush()
    _ = (out_root / _BUNDLE_HASHES_NAME).write_text(  # nosemgrep: python.no-file-writes
        json.dumps(metadata["candidate_hashes"], indent=2) + "\n",
        encoding="utf-8",
    )
    _ = (out_root / _RUN_METADATA_NAME).write_text(  # nosemgrep: python.no-file-writes
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )


def _emit_split_summary(summary: SummaryDict, split_out: Path) -> None:
    """Persist the per-split summary and stream it to stdout."""
    _ = (split_out / _SUMMARY_NAME).write_text(  # nosemgrep: python.no-file-writes
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    _ = sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    _ = sys.stdout.flush()


def _emit_failure_lines(split: str, results: Sequence[Mapping[str, object]]) -> None:
    """Write per-failure ``FAIL`` records to stdout for log capture."""
    for line in _log_failure_lines(split, results):
        _ = sys.stdout.write(line + "\n")
    _ = sys.stdout.flush()


def _write_aggregate_summaries(all_summaries: Sequence[SummaryDict], out_root: Path) -> None:
    """Persist the aggregate summary listing next to the per-split reports."""
    _ = (out_root / _SUMMARY_NAME).write_text(  # nosemgrep: python.no-file-writes
        json.dumps(list(all_summaries), indent=2) + "\n",
        encoding="utf-8",
    )


def _promotion_exit_code(promotion_eligible: bool, all_summaries: Sequence[SummaryDict]) -> int:
    """Map a promotion decision and per-split scores onto an exit code."""
    if not promotion_eligible:
        return 2
    if any(summary["hard"] < _HARD_PASS_THRESHOLD for summary in all_summaries):
        return 1
    return 0


def _build_summary(  # noqa: PLR0913
    results: Sequence[Mapping[str, object]],
    split_out: Path,
    candidate: str,
    hashes: BundleHashesDict,
    non_promotable: bool,
    promotion_reason: str,
) -> SummaryDict:
    """Assemble the per-split summary via :func:`summarize`."""
    return summarize(
        candidate=candidate,
        skill_hash=str(hashes["skill"]),
        split=split_out.name.split("_")[-1],
        results=results,
        non_promotable=non_promotable,
        promotion_reason=promotion_reason,
    )


def main(argv: Sequence[str]) -> Result[int, EvalError]:
    """Validate the candidate, run every requested split, and write the report."""
    args = _build_arg_parser().parse_args(list(argv))

    preflight = _validate_cli(args)
    if not preflight.is_ok():
        return Error(preflight.error)

    candidate_dir, config_path, out_root = _resolve_paths(args)
    _ensure_out_root(out_root)

    validate_candidate_result = _validate_candidate(candidate_dir, _format_path)
    if not validate_candidate_result.is_ok():
        return Error(validate_candidate_result.error)

    skill_path = candidate_dir / _SKILL_FILENAME
    refs_dir = candidate_dir / _REFERENCES_DIRNAME
    cfg = _load_flat_config(config_path, refs_dir, args.workers)
    validate_config_result = _validate_supported_config(
        cfg, _SUPPORTED_SPLIT_DIR, _MANIFEST_NAME, _format_path
    )
    if not validate_config_result.is_ok():
        return Error(validate_config_result.error)

    adapter = _adapter_from_cfg(cfg, _shell_get_adapter)
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
        candidate_dir_display=_format_path(candidate_dir),
        config_path_display=_format_path(config_path),
        cfg=cfg,
        hashes=hashes,
        config_sha256=sha256_file(config_path),
        dataset_split_dir_display=_format_path(_SUPPORTED_SPLIT_DIR),
        dataset_manifest_sha256=sha256_file(_SUPPORTED_SPLIT_DIR / _MANIFEST_NAME),
        promotion_eligible=promotion_eligible,
        promotion_reason=promotion_reason,
    )

    _emit_metadata(metadata, out_root)

    for split in splits:
        items = selected_items(adapter, split, ids, args.kind)
        split_result = _run_split(adapter, skill, split, items, ids, out_root)
        if not split_result.is_ok():
            return Error(split_result.error)
        split_out, results = split_result.ok

        summary = _build_summary(
            results,
            split_out,
            candidate,
            hashes,
            not promotion_eligible,
            promotion_reason,
        )
        _emit_split_summary(summary, split_out)
        all_summaries.append(summary)
        _emit_failure_lines(split, results)

    _write_aggregate_summaries(all_summaries, out_root)
    return Ok(_promotion_exit_code(promotion_eligible, all_summaries))


if __name__ == "__main__":
    result = main(tuple(sys.argv[1:]))
    if result.is_ok():
        sys.exit(result.ok)
    else:
        sys.exit(1)
