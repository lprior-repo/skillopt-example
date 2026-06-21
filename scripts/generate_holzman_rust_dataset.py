#!/usr/bin/env python3
"""Generate the aggressive Holzman Rust SkillOpt dataset splits.

Pure functional core that builds review and repair tasks, partitions them
across train/val/test splits, and serialises the result as JSON. The only
side effects live in :func:`main`.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import msgspec
from beartype import beartype
from expression import Ok, Result

# --- Domain errors ---


@dataclass(frozen=True, slots=True)
class DomainError:
    """Typed error returned from :func:`main` on shell failure."""

    code: str
    message: str


# --- Paths and constants ---


_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_DEFAULT_OUT: Final[Path] = _ROOT / "data" / "holzman_rust_aggressive"
_DEFAULT_SEED: Final[int] = 42
_DOMAINS: Final[tuple[str, ...]] = tuple(f"case{index:02d}" for index in range(20))
_DOMAIN_PATTERN: Final[str] = "|".join(_DOMAINS)
_COUNT_KEYS: Final[tuple[str, ...]] = ("total", "review", "repair")
_SPLIT_RATIOS: Final[Mapping[str, float]] = {
    "train": 0.60,
    "val": 0.20,
    "test": 0.20,
}
_SPLIT_NAMES: Final[tuple[str, ...]] = tuple(_SPLIT_RATIOS.keys())
_SPLIT_FAMILY_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(rf"^(repair_csv)_({_DOMAIN_PATTERN})_(.+)$"),
    re.compile(rf"^(repair_summary)_({_DOMAIN_PATTERN})_(.+)$"),
    re.compile(rf"^(repair_frame)_({_DOMAIN_PATTERN})_(.+)$"),
    re.compile(rf"^(repair_holzman_header)_({_DOMAIN_PATTERN})_(.+)$"),
    re.compile(rf"^(repair_functional_registration)_({_DOMAIN_PATTERN})_(.+)$"),
    re.compile(rf"^(review_hidden_io)_({_DOMAIN_PATTERN})_(.+)$"),
    re.compile(rf"^(review_invalid_state)_({_DOMAIN_PATTERN})_(.+)$"),
    re.compile(rf"^(review_black_hat)_({_DOMAIN_PATTERN})_(.+)$"),
    re.compile(rf"^(review_functional)_({_DOMAIN_PATTERN})_(.+)$"),
)
_PERF_FOLKLORE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^review_perf_folklore_[a-z]+_(.+)$")
_CARGO_DEPS_HEADER: Final[str] = '[package]\nname = "{name}"\nversion = "0.1.0"\nedition = "2021"\n'
_INT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*[+-]?\d+\s*")
_FLOAT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*[+-]?\d+(?:\.\d+)?\s*")
_U64_MAX: Final[str] = "18446744073709551615"
_PERF_FOLKLORE_SIZES: Final[tuple[str, ...]] = ("four", "tiny", "small", "fixed")
_REVIEW_KINDS: Final[tuple[str, ...]] = ("review",)
_REPAIR_KINDS: Final[tuple[str, ...]] = ("repair",)


# --- Types ---


class FileSpec(msgspec.Struct, frozen=True):
    """Placeholder struct for future per-file task metadata."""


class ForbiddenPattern(msgspec.Struct, frozen=True):
    """Raw JSON-serialisable forbidden-pattern descriptor."""

    name: str
    pattern: str


class TaskDict(msgspec.Struct, frozen=True):
    """A single review or repair task consumed by the SkillOpt harness."""

    id: str
    kind: str
    family_id: str
    domain_family_id: str
    split_family_id: str
    task_type: str
    description: str
    files: Mapping[str, str]
    doctrines: Sequence[str]
    expected_output_groups: Sequence[Sequence[str]]
    expected_source_groups: Sequence[Sequence[str]]
    forbidden_source_patterns: Sequence[ForbiddenPattern]
    forbidden_output_patterns: Sequence[ForbiddenPattern]


class ManifestDict(msgspec.Struct, frozen=True):
    """Top-level manifest describing the generated dataset splits."""

    seed: int
    total_tasks: int
    splits: Mapping[str, int]
    families: Sequence[str]
    split_families: Mapping[str, Sequence[str]]


class CountsDict(msgspec.Struct, frozen=True):
    """Aggregate task counts for a single split or family."""

    total: int
    review: int
    repair: int


@dataclass(frozen=True, slots=True)
class ForbiddenSpec:
    """Compiled forbidden-pattern descriptor with a pre-built regex."""

    name: str
    pattern: re.Pattern[str]

    @staticmethod
    @beartype
    def from_dict(spec: ForbiddenPattern) -> ForbiddenSpec:
        """Compile a raw :class:`ForbiddenPattern` into a :class:`ForbiddenSpec`."""
        return ForbiddenSpec(name=spec.name, pattern=re.compile(spec.pattern))


# --- Forbidden pattern constants ---


_LIVE_REF_FORBIDDEN: Final[tuple[ForbiddenPattern, ...]] = (
    ForbiddenPattern(
        name="live_agents_reference",
        pattern=r"(?:\$HOME|~|/[^\s\"]+?)/\.(agents|opencode|claude)",
    ),
)
_CSV_FORBIDDEN: Final[tuple[ForbiddenPattern, ...]] = (
    ForbiddenPattern(name="vec_with_capacity", pattern=r"Vec::with_capacity"),
    ForbiddenPattern(
        name="split_collect",
        pattern=r"split\s*\([^)]*\)[\s\S]{0,160}collect\s*\(",
    ),
    ForbiddenPattern(name="unchecked_count_increment", pattern=r"\bcount\s*\+="),
    ForbiddenPattern(name="lossy_as_conversion", pattern=r"\bas\s+(u16|u32|u64|usize)"),
    ForbiddenPattern(name="parts_indexing", pattern=r"\bparts\s*\["),
)
_FRAME_FORBIDDEN: Final[tuple[ForbiddenPattern, ...]] = (
    ForbiddenPattern(name="vec_with_capacity", pattern=r"Vec::with_capacity"),
    ForbiddenPattern(name="lossy_as_conversion", pattern=r"\bas\s+(u16|u32|u64|usize)"),
    ForbiddenPattern(
        name="unchecked_capacity_arithmetic",
        pattern=r"\b(payload\.len\(\)|header_size|capacity)\s*\+",
    ),
)
_SUMMARY_FORBIDDEN: Final[tuple[ForbiddenPattern, ...]] = (
    ForbiddenPattern(
        name="split_collect",
        pattern=r"split\s*\([^)]*\)[\s\S]{0,160}collect\s*\(",
    ),
    ForbiddenPattern(name="parts_indexing", pattern=r"\bparts\s*\["),
    ForbiddenPattern(name="unchecked_count_increment", pattern=r"\bcount\s*\+="),
    ForbiddenPattern(name="unchecked_total_increment", pattern=r"\btotal\s*\+="),
    ForbiddenPattern(name="lossy_as_conversion", pattern=r"\bas\s+(u16|u32|u64|usize)"),
    ForbiddenPattern(name="unchecked_division_by_count", pattern=r"/\s*count"),
    ForbiddenPattern(
        name="decimal_from_str_radix",
        pattern=r"from_str_radix\s*\([^)]*,\s*10\s*\)",
    ),
    ForbiddenPattern(
        name="discarded_name_trim",
        pattern=r"let\s+_\s*=\s*[A-Za-z_][A-Za-z0-9_]*\.trim\s*\(\s*\)",
    ),
)
_HEADER_FORBIDDEN: Final[tuple[ForbiddenPattern, ...]] = (
    ForbiddenPattern(name="unchecked_indexing", pattern=r"\binput\s*\["),
    ForbiddenPattern(name="lossy_as_conversion", pattern=r"\bas\s+(u16|u32|u64|usize)"),
    ForbiddenPattern(name="unchecked_add_or_shift_sum", pattern=r"\+"),
)
_REGISTRATION_FORBIDDEN: Final[tuple[ForbiddenPattern, ...]] = (
    ForbiddenPattern(name="public_raw_email", pattern=r"pub\s+email\s*:\s*String"),
    ForbiddenPattern(name="lifecycle_bool", pattern=r"is_active\s*:\s*bool"),
    ForbiddenPattern(
        name="option_state_machine",
        pattern=r"activated_at_epoch_ms\s*:\s*Option\s*<",
    ),
    ForbiddenPattern(name="unwrap_or_family", pattern=r"\.unwrap_or(?:_else|_default)?\s*\("),
    ForbiddenPattern(name="imperative_loop", pattern=r"\b(for|while|loop)\b"),
    ForbiddenPattern(name="mutable_binding", pattern=r"\blet\s+mut\b"),
    ForbiddenPattern(name="hidden_io", pattern=r"\b(std::fs|fs::|println!|eprintln!|env::var)"),
)
_BLACK_HAT_FORBIDDEN_OUTPUT: Final[tuple[ForbiddenPattern, ...]] = (
    ForbiddenPattern(
        name="approval_verdict",
        pattern=(
            r"(?i)\"(?:verdict|decision|result)\"\s*:\s*"
            r"\"[^\"]*(approve|approved|approval|lgtm|accept|accepted|pass|passed)"
        ),
    ),
)
_DEFAULT_DOCTRINES: Final[tuple[str, ...]] = ("holzman-rust", "functional-rust")
_BLACK_HAT_DOCTRINES: Final[tuple[str, ...]] = (
    "black-hat-reviewer",
    "holzman-rust",
    "functional-rust",
)


# --- Coercion helpers (pure, regex-based to avoid try/except) ---


@beartype
def _as_float(value: object, default: float) -> float:
    """Coerce an arbitrary value to ``float``, falling back to ``default``."""
    if isinstance(value, str) and _FLOAT_PATTERN.fullmatch(value):
        return float(value)
    match value:
        case bool():
            return float(int(value))
        case int() | float():
            return float(value)
        case _:
            pass
    return default


# --- Pure string and identifier helpers ---


@beartype
def cargo_toml(name: str, deps: str = "") -> str:
    """Render the ``Cargo.toml`` header for a task with the given crate ``name``."""
    return _CARGO_DEPS_HEADER.format(name=name) + deps


@beartype
def split_family_id(task_id: str) -> str:
    """Reduce a fully-qualified task id to its split-stable family key."""
    for pattern in _SPLIT_FAMILY_PATTERNS:
        matched = pattern.match(task_id)
        if matched is not None:
            return f"{matched.group(1)}_{matched.group(3)}"
    perf = _PERF_FOLKLORE_PATTERN.match(task_id)
    if perf is not None:
        return f"review_perf_folklore_{perf.group(1)}"
    return task_id


def _task_family_key(task: TaskDict) -> str:
    """Return the family key used to group a task within a split."""
    return task.split_family_id or task.family_id


# --- Test and expected-token builders (pure) ---


@beartype
def csv_tests(task_id: str, parse_fn: str) -> str:
    """Render the Rust behaviour test suite for a CSV ``parse_fn`` task."""
    return (
        f"use {task_id}::{{{parse_fn}, ParseError}};\n\n"
        f"#[test]\n"
        f'fn parses_values() {{ assert_eq!({parse_fn}("1,2,3", 4), Ok(vec![1, 2, 3])); }}\n'
        f"#[test]\n"
        f'fn rejects_empty() {{ assert_eq!({parse_fn}("", 4), Err(ParseError::Empty)); }}\n'
        f"#[test]\n"
        f"fn rejects_whitespace_only() {{ "
        f'assert_eq!({parse_fn}("  ,  ", 4), Err(ParseError::Empty)); }}\n'
        f"#[test]\n"
        f"fn rejects_empty_field() {{ "
        f'assert_eq!({parse_fn}("1,,3", 4), Err(ParseError::Empty)); }}\n'
        f"#[test]\n"
        f"fn rejects_invalid() {{ "
        f'assert_eq!({parse_fn}("1,nope", 4), Err(ParseError::Invalid)); }}\n'
        f"#[test]\n"
        f"fn rejects_too_many() {{ "
        f'assert_eq!({parse_fn}("1,2,3", 2), Err(ParseError::TooMany)); }}\n'
    )


@beartype
def csv_expected() -> Sequence[Sequence[str]]:
    """Return the expected token groups a correct CSV parser must mention."""
    return (
        ("try_reserve",),
        ("Vec::new",),
        ("map_err", "match"),
        ("TooMany",),
        ("Invalid",),
        ("Empty",),
        ("Allocation",),
    )


@beartype
def summary_tests(task_id: str) -> str:
    """Render the behaviour test suite for a ``summarize_rows`` task."""
    return (
        f"use {task_id}::{{render_summary, summarize_rows, Summary, SummaryError}};\n\n"
        f"#[test]\n"
        f"fn summarizes() {{ "
        f'assert_eq!(summarize_rows("a,10\\nb,5", 8), '
        f"Ok(Summary {{ count: 2, total: 15, average: 7 }})); }}\n"
        f"#[test]\n"
        f"fn renders() {{ "
        f"assert_eq!(render_summary(Summary {{ count: 2, total: 15, average: 7 }}), "
        f'"count=2 total=15 average=7"); }}\n'
        f"#[test]\n"
        f"fn rejects_empty() {{ "
        f'assert_eq!(summarize_rows("", 8), Err(SummaryError::Empty)); }}\n'
        f"#[test]\n"
        f"fn rejects_invalid() {{ "
        f'assert_eq!(summarize_rows("bad", 8), Err(SummaryError::Invalid)); }}\n'
        f"#[test]\n"
        f"fn rejects_too_many() {{ "
        f'assert_eq!(summarize_rows("a,1\\nb,2", 1), Err(SummaryError::TooMany)); }}\n'
        f"#[test]\n"
        f"fn detects_overflow() {{ "
        f'assert_eq!(summarize_rows("a,{_U64_MAX}\\nb,1", 4), '
        f"Err(SummaryError::Overflow)); }}\n"
    )


@beartype
def summary_expected() -> Sequence[Sequence[str]]:
    """Return the expected token groups for a correct summary task solution."""
    return (
        ("Summary",),
        ("render_summary",),
        ("split_once",),
        ("checked_add",),
        ("checked_div",),
        ("u64::try_from", "try_from"),
        ("u32::try_from", "try_from"),
        ("Invalid",),
        ("TooMany",),
        ("Overflow",),
    )


@beartype
def frame_tests(task_id: str) -> str:
    """Render the behaviour test suite for an ``encode_frame`` task."""
    return (
        f"use {task_id}::{{encode_frame, FrameError}};\n\n"
        f"#[test]\n"
        f"fn encodes() {{ "
        f"assert_eq!(encode_frame(b\"abc\", 8), Ok(vec![0, 0, 0, 3, b'a', b'b', b'c'])); }}\n"
        f"#[test]\n"
        f"fn rejects_limit() {{ "
        f'assert_eq!(encode_frame(b"abcdef", 3), Err(FrameError::PayloadTooLarge)); }}\n'
    )


@beartype
def frame_expected() -> Sequence[Sequence[str]]:
    """Return the expected token groups for a correct frame encoder solution."""
    return (
        ("try_reserve",),
        ("checked_add",),
        ("u32::try_from", "try_from"),
        ("PayloadTooLarge",),
        ("Allocation",),
        ("Overflow",),
    )


@beartype
def header_tests(task_id: str) -> str:
    """Render the behaviour test suite for a ``decode_len`` task."""
    return (
        f"use {task_id}::{{decode_len, HeaderError}};\n\n"
        f"#[test]\n"
        f"fn decodes_len() {{ assert_eq!(decode_len(&[0, 0, 0, 5], 8), Ok(5)); }}\n"
        f"#[test]\n"
        f"fn rejects_short() {{ "
        f"assert_eq!(decode_len(&[0, 1, 2], 8), Err(HeaderError::TooShort)); }}\n"
        f"#[test]\n"
        f"fn rejects_too_large() {{ "
        f"assert_eq!(decode_len(&[0, 0, 0, 9], 8), Err(HeaderError::TooLarge)); }}\n"
    )


@beartype
def header_expected() -> Sequence[Sequence[str]]:
    """Return the expected token groups for a correct header decoder solution."""
    return (
        ("HeaderError",),
        ("TooShort",),
        ("TooLarge",),
        ("get",),
        ("try_into",),
        ("from_be_bytes",),
        ("Result",),
    )


@beartype
def registration_tests(task_id: str) -> str:
    """Render the behaviour test suite for a user-registration task."""
    return (
        f"use {task_id}::{{activate_user, RegistrationError}};\n\n"
        f"#[test]\n"
        f"fn activates_valid_email() {{\n"
        f'    let user = activate_user("ada@example.com", 42).unwrap();\n'
        f'    assert_eq!(user.email(), "ada@example.com");\n'
        f"    assert_eq!(user.activated_at_epoch_ms(), 42);\n"
        f"}}\n\n"
        f"#[test]\n"
        f"fn rejects_missing_at() {{\n"
        f"    assert_eq!(\n"
        f'        activate_user("not-an-email", 42),\n'
        f"        Err(RegistrationError::InvalidEmail),\n"
        f"    );\n"
        f"}}\n\n"
        f"#[test]\n"
        f"fn rejects_missing_domain() {{\n"
        f"    assert_eq!(\n"
        f'        activate_user("ada@", 42),\n'
        f"        Err(RegistrationError::InvalidEmail),\n"
        f"    );\n"
        f"}}\n"
    )


@beartype
def registration_expected() -> Sequence[Sequence[str]]:
    """Return the expected token groups for a correct registration solution."""
    return (
        ("Email",),
        ("ActiveUser",),
        ("RegistrationError",),
        ("InvalidEmail",),
        ("parse",),
        ("Result",),
        ("activated_at_epoch_ms",),
        ("enum", "struct"),
    )


@beartype
def black_hat_expected() -> Sequence[Sequence[str]]:
    """Return the expected token groups a black-hat review must surface."""
    return (
        ("contract", "parity"),
        ("test", "parity"),
        ("ignored", "commented-out", "coverage"),
        ("more than 5", "5 parameters", "parameters"),
        ("25 lines", "function over", "too long"),
        ("Functional Core", "Imperative Shell", "hidden I/O"),
        ("enum", "typestate", "state machine"),
        ("String", "bool", "newtype"),
        ("parse", "boundary"),
        ("trait", "YAGNI", "one implementer"),
        ("unwrap", "panic vector", "panic"),
        ("checked", "as", "arithmetic"),
        ("REJECT", "reject"),
    )


@beartype
def black_hat_contract(domain: str) -> str:
    """Render the markdown contract that anchors a black-hat review task."""
    return (
        f"# {domain.title()} Contract\n\n"
        f"- `process_{domain}_contract` must be pure calculation code. "
        f"File I/O and contract loading belong in the shell\n"
        f"- Input must be parsed into domain types: `UserId`, `Amount`, `Region`, "
        f"`WorkflowState`, and `RetryLimit`\n"
        f"- Empty user ids must return a typed domain error, never panic\n"
        f"- The workflow state must be an enum. "
        f"Status strings and lifecycle booleans are invalid\n"
        f"- The function must not expose a dry-run future hook\n"
        f"- The output contract is `{{user_id}}:approved` for accepted requests\n"
        f"- Rejection must use a typed error, not `String`\n"
    )


@beartype
def black_hat_tests(task_id: str, domain: str) -> str:
    """Render the behaviour test suite that anchors a black-hat review task."""
    return (
        f"use {task_id}::process_{domain}_contract;\n\n"
        f"#[test]\n"
        f"fn contract_output_shape() {{\n"
        f"    assert_eq!(\n"
        f"        process_{domain}_contract("
        f'"ada".to_string(), 10, "eu".to_string(), "new".to_string(), 0, false),\n'
        f'        Ok("ada:approved".to_string())\n'
        f"    );\n"
        f"}}\n\n"
        f"#[test]\n"
        f'#[ignore = "current implementation panics instead of typed error"]\n'
        f"fn empty_user_returns_error() {{\n"
        f"    assert!(process_{domain}_contract("
        f'"".to_string(), 10, "eu".to_string(), "new".to_string(), 0, false).is_err());\n'
        f"}}\n\n"
        f"// Missing: typed-domain constructor tests for UserId, Amount, Region, "
        f"WorkflowState, RetryLimit\n"
    )


# --- Task factories (pure) ---


@beartype
def review_task(  # noqa: PLR0913
    task_id: str,
    family: str,
    src: str,
    expected: Sequence[Sequence[str]],
    forbidden_output: Sequence[ForbiddenPattern] | None = None,
    doctrines: Sequence[str] | None = None,
    extra_files: Mapping[str, str] | None = None,
) -> TaskDict:
    """Assemble a review-only :class:`TaskDict` with the given source and rubric."""
    split_key = split_family_id(task_id)
    extra_forbidden: tuple[ForbiddenPattern, ...] = (
        tuple(forbidden_output) if forbidden_output is not None else ()
    )
    merged_files: dict[str, str] = {
        "Cargo.toml": cargo_toml(task_id),
        "src/lib.rs": src,
    }
    if extra_files:
        merged_files.update(extra_files)
    return TaskDict(
        id=task_id,
        kind="review",
        family_id=split_key,
        domain_family_id=family,
        split_family_id=split_key,
        task_type="review",
        description=f"Review {family} for Holzman + functional-core Rust violations",
        files=merged_files,
        doctrines=doctrines or _DEFAULT_DOCTRINES,
        expected_output_groups=tuple(tuple(group) for group in expected),
        expected_source_groups=(),
        forbidden_source_patterns=(),
        forbidden_output_patterns=(*_LIVE_REF_FORBIDDEN, *extra_forbidden),
    )


@beartype
def repair_task(  # noqa: PLR0913
    task_id: str,
    family: str,
    src: str,
    tests: str,
    expected: Sequence[Sequence[str]],
    forbidden_source: Sequence[ForbiddenPattern] | None = None,
    forbidden_output: Sequence[ForbiddenPattern] | None = None,
    doctrines: Sequence[str] | None = None,
) -> TaskDict:
    """Assemble a repair :class:`TaskDict` with source, tests, and rubric."""
    split_key = split_family_id(task_id)
    source_tuple: tuple[ForbiddenPattern, ...] = (
        tuple(forbidden_source) if forbidden_source is not None else ()
    )
    extra_forbidden: tuple[ForbiddenPattern, ...] = (
        tuple(forbidden_output) if forbidden_output is not None else ()
    )
    return TaskDict(
        id=task_id,
        kind="repair",
        family_id=split_key,
        domain_family_id=family,
        split_family_id=split_key,
        task_type="repair",
        description=(
            f"Repair {family} while preserving tests and Holzman + functional-core constraints"
        ),
        files={
            "Cargo.toml": cargo_toml(task_id),
            "src/lib.rs": src,
            "tests/behavior.rs": tests,
        },
        doctrines=doctrines or _DEFAULT_DOCTRINES,
        expected_output_groups=(),
        expected_source_groups=tuple(tuple(group) for group in expected),
        forbidden_source_patterns=source_tuple,
        forbidden_output_patterns=(*_LIVE_REF_FORBIDDEN, *extra_forbidden),
    )


# --- Per-domain task builders (pure, return new sequences) ---


@beartype
def _review_hidden_io_tasks(domain: str) -> Sequence[TaskDict]:
    """Build review tasks that catch hidden I/O inside pure parsers."""
    family = f"review_hidden_io_{domain}"
    src = (
        f"use std::fs;\n\n"
        f"pub struct Record {{\n"
        f"    pub name: String,\n"
        f"    pub value: u16,\n"
        f"}}\n\n"
        f"pub fn load_{domain}s(path: &str) -> Vec<Record> {{\n"
        f"    let text = fs::read_to_string(path).unwrap();\n"
        f"    text.lines().map(|line| {{\n"
        f"        let parts: Vec<String> = "
        f"line.split(',').map(|part| part.trim().to_string()).collect();\n"
        f'        println!("loaded {{}}", parts[0]);\n'
        f"        Record {{ name: parts[0].clone(), value: parts[1].parse::<u32>().unwrap() "
        f"as u16 }}\n"
        f"    }}).collect()\n"
        f"}}\n"
    )
    src_variant = (
        f"use std::fs;\n\n"
        f"pub struct Record {{\n"
        f"    pub name: String,\n"
        f"    pub value: u16,\n"
        f"}}\n\n"
        f"pub fn load_{domain}_frames(path: &str) -> Vec<Record> {{\n"
        f"    let text = fs::read_to_string(path).unwrap();\n"
        f"    let mut records = Vec::with_capacity(text.lines().count());\n"
        f"    for line in text.lines() {{\n"
        f"        let fields: Vec<&str> = line.split(',').collect();\n"
        f'        eprintln!("loaded {{}}", fields[0]);\n'
        f"        records.push(Record "
        f"{{ name: fields[0].to_string(), value: fields[1].parse::<usize>().unwrap() "
        f"as u16 }});\n"
        f"    }}\n"
        f"    records\n"
        f"}}\n"
    )
    return (
        review_task(
            f"{family}_mixed",
            family,
            src,
            (
                ("I/O", "Actions", "read_to_string"),
                ("pure", "Calculations", "parsing"),
                ("unwrap", "panic"),
                ("String", "to_string", "allocation"),
                ("as", "try_from"),
                ("index", "bounds", "get", "split_once"),
                ("typed error", "Result"),
                ("try_reserve", "bounded"),
            ),
        ),
        review_task(
            f"{family}_precollect_frame",
            family,
            src_variant,
            (
                ("I/O", "Actions", "read_to_string"),
                ("pure", "Calculations", "parsing"),
                ("unwrap", "panic"),
                ("String", "to_string", "allocation"),
                ("as", "try_from"),
                ("index", "bounds", "get", "split_once"),
                ("typed error", "Result"),
                ("try_reserve", "bounded"),
            ),
        ),
    )


@beartype
def _review_invalid_state_tasks(domain: str) -> Sequence[TaskDict]:
    """Build review tasks that catch invalid-state modelling (strings, bools, Options)."""
    family = f"review_invalid_state_{domain}"
    src = (
        f"pub struct {domain.title()}Workflow {{\n"
        f"    pub id: String,\n"
        f"    pub status: String,\n"
        f"    pub is_validated: bool,\n"
        f"    pub is_sent: bool,\n"
        f"    pub sent_at_epoch_ms: Option<u64>,\n"
        f"}}\n\n"
        f"pub fn mark_sent(mut item: {domain.title()}Workflow) -> {domain.title()}Workflow {{\n"
        f'    item.status = "sent".to_string();\n'
        f"    item.is_sent = true;\n"
        f"    item\n"
        f"}}\n"
    )
    src_variant = (
        f"pub struct {domain.title()}Record {{\n"
        f"    pub id: u64,\n"
        f"    pub state: Option<String>,\n"
        f"    pub is_open: bool,\n"
        f"    pub is_closed: bool,\n"
        f"    pub closed_at_epoch_ms: Option<u64>,\n"
        f"}}\n\n"
        f"pub fn close(mut item: {domain.title()}Record) -> {domain.title()}Record {{\n"
        f'    item.state = Some("closed".to_string());\n'
        f"    item.is_closed = true;\n"
        f"    item\n"
        f"}}\n"
    )
    return (
        review_task(
            f"{family}_typestate",
            family,
            src,
            (
                ("enum", "typestate", "state machine"),
                ("status", "String"),
                ("bool", "lifecycle"),
                ("Option", "invalid state"),
                ("newtype", "domain"),
                ("parse", "boundary"),
            ),
        ),
        review_task(
            f"{family}_optional_state",
            family,
            src_variant,
            (
                ("enum", "typestate", "state machine"),
                ("status", "String", "state"),
                ("bool", "lifecycle"),
                ("Option", "invalid state"),
                ("newtype", "domain"),
                ("parse", "boundary"),
            ),
        ),
    )


@beartype
def _review_perf_folklore_tasks() -> Sequence[TaskDict]:
    """Build review tasks that flag premature Rayon/SmallVec folklore."""
    src = (
        "pub fn classify_four(bytes: &[u8; 4]) -> Vec<&'static str> {\n"
        "    // TODO: use Rayon and SmallVec because it will be faster\n"
        '    bytes.iter().map(|byte| if *byte & 1 == 0 { "even" } else { "odd" }).collect()\n'
        "}\n"
    )
    return tuple(
        review_task(
            f"review_perf_folklore_{size}_rayon_smallvec",
            f"review_perf_folklore_{size}",
            src,
            (
                ("Rayon", "parallel"),
                ("SmallVec", "smallvec"),
                ("tiny", "fixed-size", "overhead"),
                ("benchmark", "baseline"),
                ("allocation", "Vec", "collect"),
                ("array", "[&'static str; 4]"),
            ),
        )
        for size in _PERF_FOLKLORE_SIZES
    )


@beartype
def _review_unsafe_tasks() -> Sequence[TaskDict]:
    """Build review tasks that flag unjustified ``unsafe`` usage in Rust code."""
    unsafe_cases: Mapping[str, str] = {
        "transmute_header": (
            "pub fn read_len(input: &[u8]) -> u32 {\n"
            "    unsafe { std::mem::transmute::<[u8; 4], u32>("
            "[input[0], input[1], input[2], input[3]]) }\n"
            "}\n"
        ),
        "unchecked_slice": (
            "pub fn field(input: &[u8], start: usize, len: usize) -> &[u8] {\n"
            "    unsafe { input.get_unchecked(start..start + len) }\n"
            "}\n"
        ),
        "simd_tail": (
            '#[cfg(target_arch = "x86_64")]\n'
            "pub fn sum(input: &[f32]) -> f32 {\n"
            "    unsafe {\n"
            "        use std::arch::x86_64::*;\n"
            "        let mut acc = _mm_setzero_ps();\n"
            "        let mut i = 0;\n"
            "        while i < input.len() {\n"
            "            acc = _mm_add_ps(acc, _mm_loadu_ps(input.as_ptr().add(i)));\n"
            "            i += 4;\n"
            "        }\n"
            "        let mut out = [0.0; 4];\n"
            "        _mm_storeu_ps(out.as_mut_ptr(), acc);\n"
            "        out.iter().sum()\n"
            "    }\n"
            "}\n"
        ),
    }
    return tuple(
        review_task(
            family,
            family,
            src,
            (
                ("unsafe", "waiver"),
                ("bounds", "get", "chunks"),
                ("scalar", "fallback"),
                ("target", "feature"),
                ("benchmark", "evidence"),
            ),
        )
        for name, src in unsafe_cases.items()
        for family in (f"review_unsafe_{name}",)
    )


@beartype
def _review_black_hat_tasks(domain: str) -> Sequence[TaskDict]:
    """Build the three black-hat review tasks for the given ``domain``."""
    family = f"review_black_hat_{domain}"
    type_name = f"{domain.title()}PolicyHook"
    src = (
        f"use std::fs;\n\n"
        f"pub trait {type_name} {{\n"
        f"    fn score(&self, user_id: &str, amount: u64) -> u64;\n"
        f"}}\n\n"
        f"pub struct Default{type_name};\n\n"
        f"impl {type_name} for Default{type_name} {{\n"
        f"    fn score(&self, user_id: &str, amount: u64) -> u64 {{\n"
        f"        amount + user_id.len() as u64\n"
        f"    }}\n"
        f"}}\n\n"
        f"pub fn process_{domain}_contract(\n"
        f"    user_id: String,\n"
        f"    amount: u64,\n"
        f"    region: String,\n"
        f"    status: String,\n"
        f"    retries: u32,\n"
        f"    dry_run: bool,\n"
        f") -> Result<String, String> {{\n"
        f'    let contract = fs::read_to_string("contract-spec.md").unwrap_or_default();\n'
        f"    let plugin = Default{type_name};\n"
        f"    let mut score = plugin.score(&user_id, amount);\n"
        f'    if region == "eu" {{ score += 1; }}\n'
        f'    if region == "us" {{ score += 2; }}\n'
        f'    if region == "apac" {{ score += 3; }}\n'
        f'    if region == "latam" {{ score += 4; }}\n'
        f'    if status == "new" {{ score += 3; }}\n'
        f'    if status == "trusted" {{ score += 4; }}\n'
        f'    if status == "manual" {{ score += 5; }}\n'
        f'    if status == "legacy" {{ score += 6; }}\n'
        f"    if retries > 0 {{ score += retries as u64; }}\n"
        f"    if retries > 3 {{ score += 7; }}\n"
        f'    if contract.contains("strict") {{ score += 10; }}\n'
        f'    if contract.contains("trace") {{ score += 11; }}\n'
        f'    if dry_run {{ return Ok("future-hook".to_string()); }}\n'
        f'    if score > 99 {{ return Err("blocked".to_string()); }}\n'
        f'    if user_id.is_empty() {{ panic!("missing user"); }}\n'
        f'    Ok(format!("{{}}:{{}}", user_id, score))\n'
        f"}}\n"
    )
    task_id = f"{family}_contract_parity"
    contract_parity = review_task(
        task_id,
        family,
        src,
        black_hat_expected(),
        forbidden_output=_BLACK_HAT_FORBIDDEN_OUTPUT,
        doctrines=_BLACK_HAT_DOCTRINES,
        extra_files={
            "contract-spec.md": black_hat_contract(domain),
            "tests/behavior.rs": black_hat_tests(task_id, domain),
        },
    )
    evidence_src = (
        f"pub fn accept_{domain}(input: &str) -> String {{\n"
        f"    if input.is_empty() {{\n"
        f'        panic!("empty input");\n'
        f"    }}\n"
        f'    format!("accepted:{{}}", input)\n'
        f"}}\n"
    )
    evidence_task_id = f"{family}_evidence_laundering"
    evidence_laundering = review_task(
        evidence_task_id,
        family,
        evidence_src,
        (
            ("proof", "test", "source", "parity"),
            ("REJECTED", "rejected"),
            ("stale", "conflicted"),
            ("zero-test", "0 tests", "zero test"),
            ("ignored", "commented-out"),
            ("panic", "panic vector"),
            ("contract", "evidence"),
            ("REJECT", "reject"),
        ),
        doctrines=_BLACK_HAT_DOCTRINES,
        extra_files={
            "contract-spec.md": (
                f"# {domain.title()} Contract\n\n"
                f"- Empty input must return a typed error\n"
                f"- Accepted output must be domain type `Accepted{domain.title()}`\n"
            ),
            "proof-review.md": (
                "STATUS: REJECTED\n\nThe harness proves a copied model, not production source\n"
            ),
            "evidence/command-output.txt": (
                "running 0 tests\n\ntest result: ok. 0 passed; 0 failed; 0 ignored\n"
            ),
            "tests/behavior.rs": (
                f"use {evidence_task_id}::accept_{domain};\n\n"
                f"// #[test]\n"
                f"// fn rejects_empty() {{ "
                f'assert!(accept_{domain}("").is_err()); }}\n\n'
                f"#[test]\n"
                f'#[ignore = "not wired into CI"]\n'
                f"fn accepts_non_empty() {{\n"
                f'    assert_eq!(accept_{domain}("a"), "accepted:a".to_string());\n'
                f"}}\n"
            ),
        },
    )
    theater_src = (
        f"pub trait {domain.title()}Optimizer {{\n"
        f"    fn optimize(&self, amount: u64, enabled: bool) -> u64;\n"
        f"}}\n\n"
        f"pub struct Future{domain.title()}Optimizer;\n\n"
        f"impl {domain.title()}Optimizer for Future{domain.title()}Optimizer {{\n"
        f"    fn optimize(&self, amount: u64, enabled: bool) -> u64 {{\n"
        f"        if enabled {{ amount * 2 }} else {{ amount }}\n"
        f"    }}\n"
        f"}}\n\n"
        f"pub fn run_{domain}_fast_path(user_id: String, amount: u64, enabled: bool) -> String {{\n"
        f"    let optimizer = Future{domain.title()}Optimizer;\n"
        f"    let optimized = optimizer.optimize(amount, enabled);\n"
        f'    format!("{{}}:{{}}", user_id, optimized)\n'
        f"}}\n"
    )
    theater_task_id = f"{family}_performance_theater"
    performance_theater = review_task(
        theater_task_id,
        family,
        theater_src,
        (
            ("benchmark", "profiler", "evidence"),
            ("performance", "claim"),
            ("proof", "test", "source", "parity"),
            ("weak", "assert", "implementation detail"),
            ("trait", "YAGNI", "one implementer"),
            ("String", "bool", "newtype"),
            ("checked", "arithmetic", "overflow"),
            ("REJECT", "reject"),
        ),
        forbidden_output=_BLACK_HAT_FORBIDDEN_OUTPUT,
        doctrines=_BLACK_HAT_DOCTRINES,
        extra_files={
            "contract-spec.md": (
                f"# {domain.title()} Fast Path Contract\n\n"
                f"- Performance claims require benchmark and profiler evidence\n"
                f"- Inputs must use `UserId`, `Amount`, and a workflow enum, "
                f"not `String` and `bool`\n"
                f"- Arithmetic must be checked and return typed errors\n"
            ),
            "benchmark-output.txt": ("APPROVED: faster by vibes, no command output captured\n"),
            "proof-review.md": (
                "STATUS: APPROVED\nNo source-linked proof obligations were checked\n"
            ),
            "tests/behavior.rs": (
                f"use {theater_task_id}::run_{domain}_fast_path;\n\n"
                f"#[test]\n"
                f"fn contains_user_id() {{\n"
                f"    assert!(run_{domain}_fast_path("
                f'"ada".to_string(), 5, true).contains("ada"));\n'
                f"}}\n"
            ),
        },
    )
    return (contract_parity, evidence_laundering, performance_theater)


@beartype
def _review_functional_tasks(domain: str) -> Sequence[TaskDict]:
    """Build the functional-core review task for the given ``domain``."""
    family = f"review_functional_{domain}"
    src = (
        f"use std::env;\n"
        f"use std::fs;\n\n"
        f"pub fn calculate_{domain}_score(raw: &str) -> u64 {{\n"
        f'    let factor = env::var("{domain.upper()}_FACTOR")'
        f'.unwrap_or_else(|_| "2".to_string());\n'
        f"    let factor = factor.parse::<u64>().unwrap_or(1);\n"
        f'    println!("scoring {{}}", raw);\n'
        f'    let _ = fs::write("last-score.txt", raw);\n'
        f"    raw.split(',')\n"
        f"        .map(|part| part.trim().parse::<u64>().unwrap_or(0))\n"
        f"        .sum::<u64>() * factor\n"
        f"}}\n"
    )
    return (
        review_task(
            f"{family}_actions_in_calc",
            family,
            src,
            (
                ("Data", "Calculations", "Actions"),
                ("env", "environment"),
                ("println", "logging"),
                ("fs::write", "I/O"),
                ("hidden I/O", "side effect"),
                ("pure", "deterministic"),
                ("parse", "boundary"),
                ("typed error", "Result"),
                ("checked", "overflow"),
                ("unwrap_or", "unwrap_or_else"),
                ("silent", "default", "swallowed"),
                ("ignored", "Result", "let _"),
                ("no swallowed errors", "swallowed errors"),
            ),
            doctrines=("functional-rust", "holzman-rust"),
        ),
    )


@beartype
def _repair_csv_tasks(domain: str) -> Sequence[TaskDict]:
    """Build the CSV-parser repair tasks for the given ``domain``."""
    family = f"repair_csv_{domain}"
    parse_fn = f"parse_{domain}s"
    src_mixed = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum ParseError { Empty, Invalid, TooMany, Allocation }\n\n"
        f"pub fn {parse_fn}(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {{\n"
        f"    let values: Vec<u16> = "
        f"input.split(',').map(|part| part.trim().parse::<u16>().unwrap()).collect();\n"
        f"    Ok(values)\n"
        f"}}\n"
    )
    task_id_mixed = f"{family}_mixed"
    src_precollect = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum ParseError { Empty, Invalid, TooMany, Allocation }\n\n"
        f"pub fn {parse_fn}(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {{\n"
        f"    let parts: Vec<&str> = input.split(',').collect();\n"
        f"    if parts.iter().all(|part| part.trim().is_empty()) {{\n"
        f"        return Err(ParseError::Empty);\n"
        f"    }}\n"
        f"    if parts.len() > max_items {{\n"
        f"        return Err(ParseError::TooMany);\n"
        f"    }}\n"
        f"    let mut values = Vec::with_capacity(parts.len());\n"
        f"    for part in parts {{\n"
        f"        let trimmed = part.trim();\n"
        f"        if trimmed.is_empty() {{\n"
        f"            continue;\n"
        f"        }}\n"
        f"        values.push(trimmed.parse::<u16>().unwrap());\n"
        f"    }}\n"
        f"    Ok(values)\n"
        f"}}\n"
    )
    task_id_precollect = f"{family}_precollect"
    src_capacity = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum ParseError { Empty, Invalid, TooMany, Allocation }\n\n"
        f"pub fn {parse_fn}(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {{\n"
        f"    if input.is_empty() {{\n"
        f"        return Err(ParseError::Empty);\n"
        f"    }}\n"
        f"    let mut values = Vec::with_capacity(max_items);\n"
        f"    let mut count = 0usize;\n"
        f"    for part in input.split(',') {{\n"
        f"        let trimmed = part.trim();\n"
        f"        if trimmed.is_empty() {{\n"
        f"            continue;\n"
        f"        }}\n"
        f"        if count >= max_items {{\n"
        f"            return Err(ParseError::TooMany);\n"
        f"        }}\n"
        f"        values.push(trimmed.parse::<u16>().unwrap());\n"
        f"        count += 1;\n"
        f"    }}\n"
        f"    Ok(values)\n"
        f"}}\n"
    )
    task_id_capacity = f"{family}_capacity_counter"
    return (
        repair_task(
            task_id_mixed,
            family,
            src_mixed,
            csv_tests(task_id_mixed, parse_fn),
            csv_expected(),
            _CSV_FORBIDDEN,
        ),
        repair_task(
            task_id_precollect,
            family,
            src_precollect,
            csv_tests(task_id_precollect, parse_fn),
            csv_expected(),
            _CSV_FORBIDDEN,
        ),
        repair_task(
            task_id_capacity,
            family,
            src_capacity,
            csv_tests(task_id_capacity, parse_fn),
            csv_expected(),
            _CSV_FORBIDDEN,
        ),
    )


@beartype
def _repair_summary_tasks(domain: str) -> Sequence[TaskDict]:
    """Build the CSV-summary repair tasks for the given ``domain``."""
    family = f"repair_summary_{domain}"
    src_mixed = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum SummaryError { Empty, Invalid, TooMany, Overflow }\n\n"
        "#[derive(Debug, Clone, Copy, PartialEq, Eq)]\n"
        "pub struct Summary { pub count: u32, pub total: u64, pub average: u64 }\n\n"
        "pub fn summarize_rows(input: &str, max_rows: usize) -> Result<String, SummaryError> {\n"
        "    let mut total = 0u64;\n"
        "    let mut count = 0usize;\n"
        "    for line in input.lines() {\n"
        "        let parts: Vec<String> = line.split(',').map(|part| "
        "part.trim().to_string()).collect();\n"
        "        let value = parts[1].parse::<u64>().unwrap();\n"
        "        total += value;\n"
        "        count += 1;\n"
        "    }\n"
        "    if count > max_rows { return Err(SummaryError::TooMany); }\n"
        '    Ok(format!("count={} total={} average={}", '
        "count as u32, total, total / count as u64))\n"
        "}\n"
    )
    tests_mixed = (
        f"use {family}_mixed::{{render_summary, summarize_rows, Summary, SummaryError}};\n\n"
        f"#[test]\n"
        f"fn summarizes() {{ "
        f'assert_eq!(summarize_rows("a,10\\nb,5", 8), '
        f"Ok(Summary {{ count: 2, total: 15, average: 7 }})); }}\n"
        f"#[test]\n"
        f"fn renders() {{ "
        f"assert_eq!(render_summary(Summary {{ count: 2, total: 15, average: 7 }}), "
        f'"count=2 total=15 average=7"); }}\n'
        f"#[test]\n"
        f"fn rejects_empty() {{ "
        f'assert_eq!(summarize_rows("", 8), Err(SummaryError::Empty)); }}\n'
        f"#[test]\n"
        f"fn rejects_invalid() {{ "
        f'assert_eq!(summarize_rows("bad", 8), Err(SummaryError::Invalid)); }}\n'
        f"#[test]\n"
        f"fn rejects_too_many() {{ "
        f'assert_eq!(summarize_rows("a,1\\nb,2", 1), Err(SummaryError::TooMany)); }}\n'
        f"#[test]\n"
        f"fn detects_overflow() {{ "
        f'assert_eq!(summarize_rows("a,{_U64_MAX}\\nb,1", 4), '
        f"Err(SummaryError::Overflow)); }}\n"
    )
    src_counter = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum SummaryError { Empty, Invalid, TooMany, Overflow }\n\n"
        "#[derive(Debug, Clone, Copy, PartialEq, Eq)]\n"
        "pub struct Summary { pub count: u32, pub total: u64, pub average: u64 }\n\n"
        "pub fn summarize_rows(input: &str, max_rows: usize) -> Result<Summary, SummaryError> {\n"
        "    if input.is_empty() { return Err(SummaryError::Empty); }\n"
        "    let mut total = 0u64;\n"
        "    let mut count = 0u32;\n"
        "    for line in input.lines() {\n"
        "        let (_, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;\n"
        "        let value = value_str.trim().parse::<u64>().unwrap();\n"
        "        total += value;\n"
        "        count += 1;\n"
        "        if count > max_rows as u32 { return Err(SummaryError::TooMany); }\n"
        "    }\n"
        "    Ok(Summary { count, total, average: total / count as u64 })\n"
        "}\n\n"
        "pub fn render_summary(s: Summary) -> String {\n"
        '    format!("count={} total={} average={}", s.count, s.total, s.average)\n'
        "}\n"
    )
    task_id_counter = f"{family}_counter_cast"
    src_radix = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum SummaryError { Empty, Invalid, TooMany, Overflow }\n\n"
        "#[derive(Debug, Clone, Copy, PartialEq, Eq)]\n"
        "pub struct Summary { pub count: u32, pub total: u64, pub average: u64 }\n\n"
        "pub fn summarize_rows(input: &str, max_rows: usize) -> Result<Summary, SummaryError> {\n"
        "    if input.is_empty() { return Err(SummaryError::Empty); }\n"
        "    let mut total = 0u64;\n"
        "    let mut count = 0usize;\n"
        "    for line in input.lines() {\n"
        "        let (name, value_str) = line.split_once(',').unwrap();\n"
        "        let _ = name.trim();\n"
        "        let value = u64::from_str_radix(value_str.trim(), 10).unwrap();\n"
        "        total = total.checked_add(value).unwrap();\n"
        "        count += 1;\n"
        "    }\n"
        "    if count > max_rows { return Err(SummaryError::TooMany); }\n"
        "    Ok(Summary { count: count as u32, total, average: total / count as u64 })\n"
        "}\n\n"
        "pub fn render_summary(s: Summary) -> String {\n"
        '    format!("count={} total={} average={}", s.count, s.total, s.average)\n'
        "}\n"
    )
    task_id_radix = f"{family}_radix_discard"
    return (
        repair_task(
            f"{family}_mixed",
            family,
            src_mixed,
            tests_mixed,
            (
                ("Summary",),
                ("render_summary",),
                ("split_once",),
                ("checked_add",),
                ("checked_div",),
                ("u64::try_from", "try_from"),
                ("u32::try_from", "try_from"),
                ("Invalid",),
                ("TooMany",),
                ("Overflow",),
            ),
            _SUMMARY_FORBIDDEN,
        ),
        repair_task(
            task_id_counter,
            family,
            src_counter,
            summary_tests(task_id_counter),
            summary_expected(),
            _SUMMARY_FORBIDDEN,
        ),
        repair_task(
            task_id_radix,
            family,
            src_radix,
            summary_tests(task_id_radix),
            summary_expected(),
            _SUMMARY_FORBIDDEN,
        ),
    )


@beartype
def _repair_frame_tasks(domain: str) -> Sequence[TaskDict]:
    """Build the binary-frame encoder repair tasks for the given ``domain``."""
    family = f"repair_frame_{domain}"
    src_mixed = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum FrameError { PayloadTooLarge, Allocation, Overflow }\n\n"
        "pub fn encode_frame(payload: &[u8], max_payload: usize) -> Result<Vec<u8>, FrameError> {\n"
        "    let mut out = Vec::new();\n"
        "    let len = payload.len() as u32;\n"
        "    out.extend_from_slice(&len.to_be_bytes());\n"
        "    out.extend_from_slice(payload);\n"
        "    Ok(out)\n"
        "}\n"
    )
    tests_mixed = (
        f"use {family}_mixed::{{encode_frame, FrameError}};\n\n"
        f"#[test]\n"
        f"fn encodes() {{ "
        f"assert_eq!(encode_frame(b\"abc\", 8), Ok(vec![0, 0, 0, 3, b'a', b'b', b'c'])); }}\n"
        f"#[test]\n"
        f"fn rejects_limit() {{ "
        f'assert_eq!(encode_frame(b"abcdef", 3), Err(FrameError::PayloadTooLarge)); }}\n'
    )
    src_capacity = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum FrameError { PayloadTooLarge, Allocation, Overflow }\n\n"
        "pub fn encode_frame(payload: &[u8], max_payload: usize) -> Result<Vec<u8>, FrameError> {\n"
        "    let _ = max_payload;\n"
        "    let capacity = 4usize + payload.len();\n"
        "    let mut out = Vec::with_capacity(capacity);\n"
        "    let len = payload.len() as u32;\n"
        "    out.extend_from_slice(&len.to_be_bytes());\n"
        "    out.extend_from_slice(payload);\n"
        "    Ok(out)\n"
        "}\n"
    )
    task_id_capacity = f"{family}_with_capacity"
    src_saturating = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum FrameError { PayloadTooLarge, Allocation, Overflow }\n\n"
        "pub fn encode_frame(payload: &[u8], _max_payload: usize) "
        "-> Result<Vec<u8>, FrameError> {\n"
        "    let capacity = 4usize.saturating_add(payload.len());\n"
        "    let mut out = Vec::with_capacity(capacity);\n"
        "    let len = u32::try_from(payload.len()).unwrap();\n"
        "    out.extend_from_slice(&len.to_be_bytes());\n"
        "    out.extend_from_slice(payload);\n"
        "    Ok(out)\n"
        "}\n"
    )
    task_id_saturating = f"{family}_saturating_capacity"
    return (
        repair_task(
            f"{family}_mixed",
            family,
            src_mixed,
            tests_mixed,
            frame_expected(),
            _FRAME_FORBIDDEN,
        ),
        repair_task(
            task_id_capacity,
            family,
            src_capacity,
            frame_tests(task_id_capacity),
            frame_expected(),
            _FRAME_FORBIDDEN,
        ),
        repair_task(
            task_id_saturating,
            family,
            src_saturating,
            frame_tests(task_id_saturating),
            frame_expected(),
            _FRAME_FORBIDDEN,
        ),
    )


@beartype
def _repair_holzman_header_tasks(domain: str) -> Sequence[TaskDict]:
    """Build the Holzman header-decoder repair tasks for the given ``domain``."""
    family = f"repair_holzman_header_{domain}"
    src = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum HeaderError { TooShort, TooLarge }\n\n"
        "pub fn decode_len(input: &[u8], max_len: u32) -> Result<u32, HeaderError> {\n"
        "    let len = ((input[0] as u32) << 24)\n"
        "        + ((input[1] as u32) << 16)\n"
        "        + ((input[2] as u32) << 8)\n"
        "        + input[3] as u32;\n"
        "    if len > max_len {\n"
        "        return Err(HeaderError::TooLarge);\n"
        "    }\n"
        "    Ok(len)\n"
        "}\n"
    )
    task_id = f"{family}_checked_boundary"
    return (
        repair_task(
            task_id,
            family,
            src,
            header_tests(task_id),
            header_expected(),
            _HEADER_FORBIDDEN,
            doctrines=("holzman-rust", "functional-rust"),
        ),
    )


@beartype
def _repair_functional_registration_tasks(domain: str) -> Sequence[TaskDict]:
    """Build the DDD-typed registration repair tasks for the given ``domain``."""
    family = f"repair_functional_registration_{domain}"
    src = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub struct User {\n"
        "    pub email: String,\n"
        "    pub is_active: bool,\n"
        "    pub activated_at_epoch_ms: Option<u64>,\n"
        "}\n\n"
        "pub fn activate_user(email: &str, now_epoch_ms: u64) -> User {\n"
        "    User {\n"
        "        email: email.to_string(),\n"
        "        is_active: true,\n"
        "        activated_at_epoch_ms: Some(now_epoch_ms),\n"
        "    }\n"
        "}\n"
    )
    task_id = f"{family}_ddd_types"
    return (
        repair_task(
            task_id,
            family,
            src,
            registration_tests(task_id),
            registration_expected(),
            _REGISTRATION_FORBIDDEN,
            doctrines=("functional-rust", "holzman-rust", "black-hat-reviewer"),
        ),
    )


# --- Build all tasks (pure, immutable accumulation) ---


@beartype
def build_tasks() -> Sequence[TaskDict]:
    """Aggregate every review and repair task across all configured domains."""
    result: tuple[TaskDict, ...] = ()
    for domain in _DOMAINS:
        result = (
            *result,
            *_review_hidden_io_tasks(domain),
            *_review_invalid_state_tasks(domain),
            *_review_black_hat_tasks(domain),
            *_review_functional_tasks(domain),
            *_repair_csv_tasks(domain),
            *_repair_summary_tasks(domain),
            *_repair_frame_tasks(domain),
            *_repair_holzman_header_tasks(domain),
            *_repair_functional_registration_tasks(domain),
        )
    return (*result, *_review_perf_folklore_tasks(), *_review_unsafe_tasks())


# --- Split logic (pure) ---


@beartype
def empty_counts() -> CountsDict:
    """Return a zero-valued :class:`CountsDict` for fresh-split accounting."""
    return CountsDict(total=0, review=0, repair=0)


@beartype
def count_items(items: Sequence[TaskDict]) -> CountsDict:
    """Tally review/repair totals across the given task sequence."""
    review = sum(1 for item in items if item.kind == "review")
    total = len(items)
    return CountsDict(total=total, review=review, repair=total - review)


@beartype
def scale_counts(counts: CountsDict, ratio: float) -> Mapping[str, float]:
    """Multiply every field of ``counts`` by ``ratio`` to get a target size."""
    return {
        "total": float(counts.total) * ratio,
        "review": float(counts.review) * ratio,
        "repair": float(counts.repair) * ratio,
    }


@beartype
def add_counts(left: CountsDict, right: CountsDict) -> CountsDict:
    """Return the field-wise sum of two :class:`CountsDict` instances."""
    return CountsDict(
        total=left.total + right.total,
        review=left.review + right.review,
        repair=left.repair + right.repair,
    )


@beartype
def projected_assignment_error(
    target_split: str,
    family_count: CountsDict,
    counts: Mapping[str, CountsDict],
    targets: Mapping[str, Mapping[str, float]],
) -> float:
    """Score how well ``family_count`` would fit into ``target_split``."""
    error = 0.0
    for split in _SPLIT_RATIOS:
        projected = (
            add_counts(counts[split], family_count) if split == target_split else counts[split]
        )
        error += relative_squared_error(projected, targets[split])
    return error


@beartype
def relative_squared_error(observed: CountsDict, target: Mapping[str, float]) -> float:
    """Sum the squared relative error between observed counts and targets."""
    error = 0.0
    for key, observed_value in (
        ("total", observed.total),
        ("review", observed.review),
        ("repair", observed.repair),
    ):
        target_value = max(1.0, _as_float(target.get(key), 0.0))
        diff = float(observed_value) - target_value
        error += (diff / target_value) ** 2
    return error


@beartype
def _split_family_keys(items: Sequence[TaskDict]) -> Sequence[str]:
    """Return the sorted unique split-family keys present in ``items``."""
    return sorted({_task_family_key(item) for item in items})


@beartype
def _family_keys(tasks: Sequence[TaskDict]) -> Sequence[str]:
    """Return the sorted unique family ids present in ``tasks``."""
    return sorted({task.family_id for task in tasks})


@beartype
def split_by_family(
    tasks: Sequence[TaskDict],
    family_order: Sequence[str],
) -> Mapping[str, Sequence[TaskDict]]:
    """Partition ``tasks`` into train/val/test while honouring :data:`_SPLIT_RATIOS`."""
    by_family: dict[str, tuple[TaskDict, ...]] = {}
    for task in tasks:
        key = _task_family_key(task)
        existing = by_family.get(key, ())
        by_family[key] = (*existing, task)
    order = {family: index for index, family in enumerate(family_order)}
    total_counts = count_items(tasks)
    targets: dict[str, Mapping[str, float]] = {
        split: scale_counts(total_counts, ratio) for split, ratio in _SPLIT_RATIOS.items()
    }
    counts: dict[str, CountsDict] = {split: empty_counts() for split in _SPLIT_RATIOS}
    preassigned: frozenset[str] = frozenset()
    black_hat_families = sorted(
        (family for family in by_family if family.startswith("review_black_hat_")),
        key=lambda family: order[family],
    )
    assigned: dict[str, tuple[str, ...]] = dict.fromkeys(_SPLIT_RATIOS, ())
    for split, family in zip(_SPLIT_NAMES, black_hat_families):  # noqa: B905
        assigned[split] = (*assigned[split], family)
        counts[split] = add_counts(counts[split], count_items(by_family[family]))
        preassigned = preassigned | {family}

    for family in sorted(by_family, key=lambda fam: (-len(by_family[fam]), order[fam])):
        if family in preassigned:
            continue
        family_count = count_items(by_family[family])
        best_split = min(
            _SPLIT_RATIOS,
            key=lambda split: (
                projected_assignment_error(split, family_count, counts, targets),
                counts[split].total,
                split,
            ),
        )
        assigned[best_split] = (*assigned[best_split], family)
        counts[best_split] = add_counts(counts[best_split], family_count)
    return {
        name: tuple(task for family in fams for task in by_family[family])
        for name, fams in assigned.items()
    }


@beartype
def _build_manifest(
    seed: int,
    tasks: Sequence[TaskDict],
    splits: Mapping[str, Sequence[TaskDict]],
) -> ManifestDict:
    """Assemble a :class:`ManifestDict` describing the generated dataset."""
    return ManifestDict(
        seed=seed,
        total_tasks=len(tasks),
        splits={split: len(items) for split, items in splits.items()},
        families=_family_keys(tasks),
        split_families={split: _split_family_keys(items) for split, items in splits.items()},
    )


# --- Shell helpers (side effects isolated here) ---


@beartype
def _shuffle_families(families: Sequence[str], seed: int) -> tuple[str, ...]:
    """Return ``families`` deterministically shuffled using ``seed``."""
    rng = random.Random(seed)  # noqa: S311
    shuffled = sorted(families)
    rng.shuffle(shuffled)
    return tuple(shuffled)


# --- Main entry point (the only function with I/O and print) ---


def main() -> Result[int, DomainError]:
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

    for split, items in splits.items():
        split_dir = out / split
        split_dir.mkdir(parents=True, exist_ok=True)
        _ = (split_dir / "items.json").write_text(
            json.dumps([msgspec.to_builtins(item) for item in items], indent=2) + "\n",
            encoding="utf-8",
        )

    manifest = _build_manifest(args.seed, tasks, splits)
    _ = (out / "manifest.json").write_text(
        json.dumps(msgspec.to_builtins(manifest), indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(msgspec.to_builtins(manifest), indent=2))  # noqa: T201
    return Ok(0)


# --- Shell entry point ---


if __name__ == "__main__":
    result = main()
    if result.is_ok():
        sys.exit(result.ok)
    else:
        sys.exit(1)
