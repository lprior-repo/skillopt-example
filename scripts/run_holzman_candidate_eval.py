#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, TypedDict, cast


class _Dataloader(Protocol):
    train_items: Sequence[Mapping[str, object]]
    val_items: Sequence[Mapping[str, object]]
    test_items: Sequence[Mapping[str, object]]


class _Adapter(Protocol):
    dataloader: _Dataloader

    def setup(self, cfg: Mapping[str, object]) -> None: ...

    def rollout(
        self,
        items: Sequence[Mapping[str, object]],
        skill: str,
        out_dir: str,
    ) -> list[dict[str, object]]: ...


class BundleHashesDict(TypedDict):
    skill: str
    references: dict[str, str]


class SummaryDict(TypedDict):
    candidate: str
    skill_sha256: str
    split: str
    n: int
    hard: float
    soft: float
    passed: int
    failed: list[str]
    fail_reasons: dict[str, str]
    model_counts: dict[str, int]
    non_promotable: bool
    promotion_reason: str


_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SKILLOPT_ROOT: Final[Path] = _ROOT / "vendor" / "SkillOpt"
_DEFAULT_CONFIG: Final[Path] = _SKILLOPT_ROOT / "configs" / "holzman_rust" / "aggressive.yaml"
_DEFAULT_CANDIDATE_DIR: Final[Path] = _ROOT / "candidates" / "holzman-rust-candidate-v13"
_DEFAULT_REPORT_ROOT: Final[Path] = _ROOT / "reports" / "skillopt-training"
_VALID_SPLITS: Final[tuple[str, ...]] = ("train", "val", "test")
_HARD_PASS_THRESHOLD: Final[float] = 1.0
_BUNDLE_HASHES_NAME: Final[str] = "bundle_hashes.json"
_SUMMARY_NAME: Final[str] = "summary.json"
_RUN_METADATA_NAME: Final[str] = "run_metadata.json"
_REFERENCES_DIRNAME: Final[str] = "references"
_SKILL_FILENAME: Final[str] = "SKILL.md"
_SUPPORTED_SPLIT_DIR: Final[Path] = _ROOT / "data" / "holzman_rust_aggressive"
_MANIFEST_NAME: Final[str] = "manifest.json"


@dataclass(frozen=True, slots=True)
class CandidatePaths:
    skill: Path
    references: Path


class RunError(Exception):
    code: str

    def __init__(self, message: str, *, code: str = "run_error") -> None:
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {super().__str__()}"


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


def _as_str(value: object, default: str) -> str:
    match value:
        case str() as s:
            return s
        case bool() | int() | float():
            return str(value)
        case _:
            return default


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def split_values(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def all_split_items(adapter: _Adapter, split: str) -> Sequence[Mapping[str, object]]:
    dataloader = adapter.dataloader
    match split:
        case "train":
            return list(dataloader.train_items)
        case "val":
            return list(dataloader.val_items)
        case "test":
            return list(dataloader.test_items)
        case _:
            raise RunError(f"unknown split: {split}", code="unknown_split")


def selected_items(
    adapter: _Adapter,
    split: str,
    ids: set[str],
    kind: str,
) -> Sequence[Mapping[str, object]]:
    items = list(all_split_items(adapter, split))
    if ids:
        items = [item for item in items if _as_str(item.get("id"), "") in ids]
    if kind != "all":
        items = [
            item
            for item in items
            if _as_str(item.get("kind") or item.get("task_type") or "review", "") == kind
        ]
    return items


def _sha256_relative(root: Path, path: Path) -> str:
    return sha256_file(path)


def bundle_hashes(candidate_dir: Path) -> BundleHashesDict:
    skill_path = candidate_dir / _SKILL_FILENAME
    refs_dir = candidate_dir / _REFERENCES_DIRNAME
    hashes: BundleHashesDict = {
        "skill": sha256_file(skill_path),
        "references": {},
    }
    if refs_dir.exists():
        for path in sorted(refs_dir.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(candidate_dir))
                hashes["references"][rel] = _sha256_relative(candidate_dir, path)
    return hashes


def _row_hard(row: Mapping[str, object]) -> float:
    return _as_float(row.get("hard", 0.0), 0.0)


def _row_soft(row: Mapping[str, object]) -> float:
    return _as_float(row.get("soft", 0.0), 0.0)


def _row_passed_p(hard_value: float) -> bool:
    return hard_value >= _HARD_PASS_THRESHOLD


def summarize(
    candidate: str,
    skill_hash: str,
    split: str,
    results: Sequence[Mapping[str, object]],
    non_promotable: bool,
    promotion_reason: str,
) -> SummaryDict:
    failures = [row for row in results if not _row_passed_p(_row_hard(row))]
    model_counts = dict(sorted(Counter(_as_str(row.get("model") or "", "") for row in results).items()))
    n = max(1, len(results))
    return SummaryDict(
        candidate=candidate,
        skill_sha256=skill_hash,
        split=split,
        n=len(results),
        hard=sum(_row_hard(row) for row in results) / n,
        soft=sum(_row_soft(row) for row in results) / n,
        passed=len(results) - len(failures),
        failed=[_as_str(row.get("id"), "") for row in failures],
        fail_reasons={
            _as_str(row.get("id"), ""): _as_str(row.get("fail_reason") or "", "") for row in failures
        },
        model_counts=model_counts,
        non_promotable=non_promotable,
        promotion_reason=promotion_reason,
    )


def _resolve_out_root(args_out: str) -> Path:
    out = Path(args_out).expanduser()
    if not out.is_absolute():
        return _DEFAULT_REPORT_ROOT / out
    return out


def _validate_candidate(candidate_dir: Path) -> None:
    skill_path = candidate_dir / _SKILL_FILENAME
    if not skill_path.is_file():
        raise RunError(f"missing skill file: {skill_path}", code="missing_skill_md")


def _config_errors(cfg: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    split_mode = _as_str(cfg.get("split_mode"), "").strip().lower()
    if split_mode != "split_dir":
        errors.append(f"split_mode={split_mode or '<empty>'}")

    split_dir = Path(_as_str(cfg.get("split_dir"), "")).expanduser()
    try:
        resolved_split_dir = split_dir.resolve()
    except OSError:
        resolved_split_dir = split_dir
    if resolved_split_dir != _SUPPORTED_SPLIT_DIR.resolve():
        errors.append(f"split_dir={resolved_split_dir}")

    if _as_str(cfg.get("data_path"), "").strip():
        errors.append("data_path_must_be_empty")
    if _as_str(cfg.get("split_output_dir"), "").strip():
        errors.append("split_output_dir_must_be_empty")
    if _as_int(cfg.get("limit"), 0) != 0:
        errors.append(f"limit={_as_int(cfg.get('limit'), 0)}")
    if not (_SUPPORTED_SPLIT_DIR / _MANIFEST_NAME).is_file():
        errors.append(f"missing_dataset_manifest={_SUPPORTED_SPLIT_DIR / _MANIFEST_NAME}")
    return errors


def _validate_supported_config(cfg: Mapping[str, object]) -> None:
    errors = _config_errors(cfg)
    if errors:
        raise RunError(
            "unsupported candidate-eval config: " + ", ".join(errors),
            code="unsupported_config",
        )


def _promotion_status(splits: Sequence[str], ids: set[str], kind: str) -> tuple[bool, str]:
    reasons: list[str] = []
    if list(splits) != ["val", "test"]:
        reasons.append("splits_must_be_val_test")
    if ids:
        reasons.append("targeted_ids_selected")
    if kind != "all":
        reasons.append(f"kind={kind}")
    if reasons:
        return False, ";".join(reasons)
    return True, "full_val_test_all_tasks"


def _validate_splits(splits: Sequence[str]) -> None:
    unknown = sorted({split for split in splits if split not in _VALID_SPLITS})
    if unknown:
        raise RunError("unknown split(s): " + ", ".join(unknown), code="unknown_split")


def _run_metadata(
    *,
    candidate: str,
    candidate_dir: Path,
    config_path: Path,
    cfg: Mapping[str, object],
    hashes: BundleHashesDict,
    promotion_eligible: bool,
    promotion_reason: str,
) -> dict[str, object]:
    manifest_path = _SUPPORTED_SPLIT_DIR / _MANIFEST_NAME
    return {
        "candidate": candidate,
        "candidate_dir": str(candidate_dir),
        "candidate_hashes": hashes,
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "dataset_split_dir": str(_SUPPORTED_SPLIT_DIR),
        "dataset_manifest_sha256": sha256_file(manifest_path),
        "promotion_eligible": promotion_eligible,
        "promotion_reason": promotion_reason,
        "review_model": _as_str(cfg.get("review_model"), ""),
        "repair_model": _as_str(cfg.get("repair_model"), ""),
        "opencode_variant": _as_str(cfg.get("opencode_variant"), ""),
        "opencode_show_thinking": bool(cfg.get("opencode_show_thinking")),
    }


def _prepare_config(config_path: Path, refs_dir: Path, workers: int) -> dict[str, object]:
    sys.path.insert(0, str(_SKILLOPT_ROOT.resolve()))
    from skillopt.config import (  # type: ignore[import-not-found]
        flatten_config,
        load_config,
    )

    cfg = flatten_config(load_config(str(config_path)))
    cfg_dict = cast(dict[str, object], cfg)
    cfg_dict["references_dir"] = str(refs_dir)
    if workers > 0:
        cfg_dict["workers"] = workers
    return cfg_dict


def _run_split(
    adapter: _Adapter,
    skill: str,
    split: str,
    items: Sequence[Mapping[str, object]],
    ids: set[str],
    out_root: Path,
) -> tuple[Path, list[dict[str, object]]]:
    if not items:
        raise RunError(f"no items selected for split={split}", code="empty_selection")
    split_out = out_root / f"full_{split}" if not ids else out_root / f"targeted_{split}"
    results = adapter.rollout(items, skill, str(split_out))
    return split_out, list(results)


def _write_summary(split_out: Path, summary: SummaryDict) -> None:
    (split_out / _SUMMARY_NAME).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def _log_failures(split: str, results: Sequence[Mapping[str, object]]) -> None:
    for row in results:
        if not _row_passed_p(_row_hard(row)):
            print(
                "FAIL",
                split,
                row.get("id"),
                row.get("fail_reason"),
                row.get("model"),
                flush=True,
            )


def _adapter_from_cfg(cfg: dict[str, object]) -> _Adapter:
    from scripts.train import get_adapter  # type: ignore[import-not-found]

    adapter = cast(_Adapter, get_adapter(cfg))
    adapter.setup(cfg)
    return adapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Run current SkillOpt Holzman candidate evaluations")
    parser.add_argument("--candidate-dir", default=str(_DEFAULT_CANDIDATE_DIR))
    parser.add_argument("--config", default=str(_DEFAULT_CONFIG))
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory under reports/skillopt-training unless absolute",
    )
    parser.add_argument("--splits", default="val,test", help="Comma-separated train,val,test")
    parser.add_argument("--ids", default="", help="Comma-separated task ids for targeted reruns")
    parser.add_argument("--kind", choices=["all", "review", "repair"], default="all")
    parser.add_argument("--candidate-name", default="", help="Label stored in summaries")
    parser.add_argument("--workers", type=int, default=0, help="Override env.workers")
    args = parser.parse_args()

    candidate_dir = Path(args.candidate_dir).expanduser().resolve()
    _validate_candidate(candidate_dir)
    skill_path = candidate_dir / _SKILL_FILENAME
    refs_dir = candidate_dir / _REFERENCES_DIRNAME
    out_root = _resolve_out_root(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    config_path = Path(args.config).expanduser().resolve()
    cfg = _prepare_config(config_path, refs_dir, args.workers)
    _validate_supported_config(cfg)
    adapter = _adapter_from_cfg(cfg)
    skill = skill_path.read_text(encoding="utf-8")
    hashes = bundle_hashes(candidate_dir)
    candidate = args.candidate_name or candidate_dir.name
    ids = set(split_values(args.ids))
    splits = split_values(args.splits)
    _validate_splits(splits)
    promotion_eligible, promotion_reason = _promotion_status(splits, ids, args.kind)
    all_summaries: list[SummaryDict] = []

    metadata = _run_metadata(
        candidate=candidate,
        candidate_dir=candidate_dir,
        config_path=config_path,
        cfg=cfg,
        hashes=hashes,
        promotion_eligible=promotion_eligible,
        promotion_reason=promotion_reason,
    )

    (out_root / _BUNDLE_HASHES_NAME).write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    (out_root / _RUN_METADATA_NAME).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"out": str(out_root), "run_metadata": metadata},
            indent=2,
        ),
        flush=True,
    )

    for split in splits:
        items = selected_items(adapter, split, ids, args.kind)
        split_out, results = _run_split(adapter, skill, split, items, ids, out_root)
        summary = summarize(
            candidate,
            str(hashes["skill"]),
            split,
            results,
            not promotion_eligible,
            promotion_reason,
        )
        _write_summary(split_out, summary)
        all_summaries.append(summary)
        print(json.dumps(summary, indent=2), flush=True)
        _log_failures(split, results)

    (out_root / _SUMMARY_NAME).write_text(json.dumps(all_summaries, indent=2) + "\n", encoding="utf-8")
    if not promotion_eligible:
        return 2
    if any(summary["hard"] < _HARD_PASS_THRESHOLD for summary in all_summaries):
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
