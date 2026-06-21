#!/usr/bin/env python3
"""Generate the aggressive Holzman Rust SkillOpt dataset splits.

Thin shell that delegates all pure logic to :mod:`scripts.dataset_core`
and confines side effects (argument parsing, seeded shuffling, JSON
serialisation, file writes, stdout) to :func:`main`.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

import msgspec
from expression import Ok, Result

from scripts.dataset_core import (
    ForbiddenPattern,
    ForbiddenSpec,
    TaskDict,
    _build_manifest,  # pyright: ignore[reportPrivateUsage]
    _family_keys,  # pyright: ignore[reportPrivateUsage]
    _shuffle_families,  # pyright: ignore[reportPrivateUsage]
    build_tasks,
    split_by_family,
    split_family_id,
)
from scripts.errors import DatasetError

__all__ = ["ForbiddenPattern", "ForbiddenSpec", "main", "split_family_id"]


_DEFAULT_OUT: Final[Path] = Path(__file__).resolve().parents[1] / "data" / "holzman_rust_aggressive"
_DEFAULT_SEED: Final[int] = 42


def _write_split(out_dir: Path, split: str, items: tuple[object, ...]) -> None:
    """Serialise ``items`` for ``split`` into ``out_dir/split/items.json``."""
    split_dir = out_dir / split
    split_dir.mkdir(parents=True, exist_ok=True)  # nosemgrep: python.no-file-writes
    _ = (split_dir / "items.json").write_text(  # nosemgrep: python.no-file-writes
        json.dumps([msgspec.to_builtins(item) for item in items], indent=2) + "\n",
        encoding="utf-8",
    )


def _write_manifest(out_dir: Path, manifest: object) -> None:
    """Serialise the dataset ``manifest`` to ``out_dir/manifest.json``."""
    _ = (out_dir / "manifest.json").write_text(  # nosemgrep: python.no-file-writes
        json.dumps(msgspec.to_builtins(manifest), indent=2) + "\n",
        encoding="utf-8",
    )


def _serialise_splits(
    out_dir: Path, splits: Mapping[str, Sequence[TaskDict]]
) -> Mapping[str, int]:  # nosemgrep: python.no-mutable-collection-annotations
    """Write per-split JSON files and return the per-split item counts."""
    counts: dict[str, int] = {}  # nosemgrep: python.no-mutable-collection-annotations
    for split, items in splits.items():
        _write_split(out_dir, split, tuple(items))
        counts[split] = len(items)
    return counts


def _emit_manifest(manifest: object) -> None:
    """Print the dataset manifest to stdout for shell consumers."""
    print(json.dumps(msgspec.to_builtins(manifest), indent=2))  # noqa: T201  # nosemgrep: python.no-print


def main() -> Result[int, DatasetError]:
    """Build tasks, split them, and serialise the dataset to ``--out``."""
    parser = argparse.ArgumentParser(
        description="Generate aggressive Holzman Rust SkillOpt dataset splits"
    )
    _ = parser.add_argument("--out", default=str(_DEFAULT_OUT))
    _ = parser.add_argument("--seed", type=int, default=_DEFAULT_SEED)
    args = parser.parse_args()

    out = Path(args.out)
    tasks = build_tasks()
    family_order = _shuffle_families(_family_keys(tasks), args.seed)
    splits = split_by_family(tasks, family_order)
    _ = _serialise_splits(out, splits)

    manifest = _build_manifest(args.seed, tasks, splits)
    _write_manifest(out, manifest)
    _emit_manifest(manifest)
    return Ok(0)


if __name__ == "__main__":
    result = main()
    if result.is_ok():
        sys.exit(result.ok)
    else:
        sys.exit(1)
