#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict, cast


class FileSpec(TypedDict):
    pass


class ForbiddenPattern(TypedDict):
    name: str
    pattern: str


class TaskDict(TypedDict, total=False):
    id: str
    kind: str
    family_id: str
    domain_family_id: str
    split_family_id: str
    task_type: str
    description: str
    files: dict[str, str]
    doctrines: list[str]
    expected_output_groups: list[list[str]]
    expected_source_groups: list[list[str]]
    forbidden_source_patterns: list[ForbiddenPattern]
    forbidden_output_patterns: list[ForbiddenPattern]


class ManifestDict(TypedDict):
    seed: int
    total_tasks: int
    splits: dict[str, int]
    families: list[str]
    split_families: dict[str, list[str]]


class CountsDict(TypedDict):
    total: int
    review: int
    repair: int


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
_LIVE_REF_FORBIDDEN: Final[tuple[ForbiddenPattern, ...]] = (
    ForbiddenPattern(
        name="live_agents_reference",
        pattern=r"/home/lewis/\.(agents|opencode|claude)",
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
        pattern=r"(?i)\"(?:verdict|decision|result)\"\s*:\s*\"[^\"]*(approve|approved|approval|lgtm|accept|accepted|pass|passed)",
    ),
)
_DEFAULT_DOCTRINES: Final[tuple[str, ...]] = ("holzman-rust", "functional-rust")
_BLACK_HAT_DOCTRINES: Final[tuple[str, ...]] = (
    "black-hat-reviewer",
    "holzman-rust",
    "functional-rust",
)
_REVIEW_KINDS: Final[tuple[str, ...]] = ("review",)
_REPAIR_KINDS: Final[tuple[str, ...]] = ("repair",)
_PERF_FOLKLORE_SIZES: Final[tuple[str, ...]] = ("four", "tiny", "small", "fixed")
_U64_MAX: Final[str] = "18446744073709551615"
_DEFAULT_DOCTRINE_REVIEW_KIND: Final[str] = "review"
_DEFAULT_DOCTRINE_REPAIR_KIND: Final[str] = "repair"


@dataclass(frozen=True, slots=True)
class ForbiddenSpec:
    name: str
    pattern: re.Pattern[str]

    @staticmethod
    def from_dict(spec: ForbiddenPattern) -> ForbiddenSpec:
        return ForbiddenSpec(name=spec["name"], pattern=re.compile(spec["pattern"]))


def _as_str(value: object, default: str) -> str:
    match value:
        case str() as s:
            return s
        case bool() | int() | float():
            return str(value)
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


def cargo_toml(name: str, deps: str = "") -> str:
    return _CARGO_DEPS_HEADER.format(name=name) + deps


def split_family_id(task_id: str) -> str:
    for pattern in _SPLIT_FAMILY_PATTERNS:
        match = pattern.match(task_id)
        if match:
            return f"{match.group(1)}_{match.group(3)}"
    perf = _PERF_FOLKLORE_PATTERN.match(task_id)
    if perf:
        return f"review_perf_folklore_{perf.group(1)}"
    return task_id


def _list_dict(payload: Mapping[str, object], key: str) -> list[ForbiddenPattern]:
    raw = payload.get(key, [])
    match raw:
        case list() as items:
            return cast(list[ForbiddenPattern], items)
        case _:
            return []


def _dict_get(payload: Mapping[str, object], key: str) -> object:
    return payload.get(key)


def _to_forbidden_dicts(
    specs: Sequence[ForbiddenPattern],
) -> list[ForbiddenPattern]:
    return [ForbiddenPattern(name=spec["name"], pattern=spec["pattern"]) for spec in specs]


def review_task(
    task_id: str,
    family: str,
    src: str,
    expected: Sequence[Sequence[str]],
    forbidden_output: Sequence[ForbiddenPattern] | None = None,
    doctrines: Sequence[str] | None = None,
    extra_files: Mapping[str, str] | None = None,
) -> TaskDict:
    files: dict[str, str] = {
        "Cargo.toml": cargo_toml(task_id),
        "src/lib.rs": src,
    }
    if extra_files:
        files.update(extra_files)
    split_key = split_family_id(task_id)
    return TaskDict(
        id=task_id,
        kind="review",
        family_id=split_key,
        domain_family_id=family,
        split_family_id=split_key,
        task_type="review",
        description=f"Review {family} for Holzman + functional-core Rust violations",
        files=files,
        doctrines=list(doctrines or _DEFAULT_DOCTRINES),
        expected_output_groups=[list(group) for group in expected],
        forbidden_source_patterns=[],
        forbidden_output_patterns=[
            *_to_forbidden_dicts(_LIVE_REF_FORBIDDEN),
            *_to_forbidden_dicts(list(forbidden_output or [])),
        ],
    )


def repair_task(
    task_id: str,
    family: str,
    src: str,
    tests: str,
    expected: Sequence[Sequence[str]],
    forbidden_source: Sequence[ForbiddenPattern] | None = None,
    forbidden_output: Sequence[ForbiddenPattern] | None = None,
    doctrines: Sequence[str] | None = None,
) -> TaskDict:
    split_key = split_family_id(task_id)
    return TaskDict(
        id=task_id,
        kind="repair",
        family_id=split_key,
        domain_family_id=family,
        split_family_id=split_key,
        task_type="repair",
        description=f"Repair {family} while preserving tests and Holzman + functional-core constraints",
        files={
            "Cargo.toml": cargo_toml(task_id),
            "src/lib.rs": src,
            "tests/behavior.rs": tests,
        },
        doctrines=list(doctrines or _DEFAULT_DOCTRINES),
        expected_source_groups=[list(group) for group in expected],
        forbidden_source_patterns=_to_forbidden_dicts(list(forbidden_source or [])),
        forbidden_output_patterns=[
            *_to_forbidden_dicts(_LIVE_REF_FORBIDDEN),
            *_to_forbidden_dicts(list(forbidden_output or [])),
        ],
    )


def csv_tests(task_id: str, parse_fn: str) -> str:
    return (
        f"use {task_id}::{{{parse_fn}, ParseError}};\n\n"
        f"#[test]\n"
        f'fn parses_values() {{ assert_eq!({parse_fn}("1,2,3", 4), Ok(vec![1, 2, 3])); }}\n'
        f"#[test]\n"
        f'fn rejects_empty() {{ assert_eq!({parse_fn}("", 4), Err(ParseError::Empty)); }}\n'
        f"#[test]\n"
        f'fn rejects_whitespace_only() {{ assert_eq!({parse_fn}("  ,  ", 4), Err(ParseError::Empty)); }}\n'
        f"#[test]\n"
        f'fn rejects_empty_field() {{ assert_eq!({parse_fn}("1,,3", 4), Err(ParseError::Empty)); }}\n'
        f"#[test]\n"
        f'fn rejects_invalid() {{ assert_eq!({parse_fn}("1,nope", 4), Err(ParseError::Invalid)); }}\n'
        f"#[test]\n"
        f'fn rejects_too_many() {{ assert_eq!({parse_fn}("1,2,3", 2), Err(ParseError::TooMany)); }}\n'
    )


def csv_expected() -> list[list[str]]:
    return [
        ["try_reserve"],
        ["Vec::new"],
        ["map_err", "match"],
        ["TooMany"],
        ["Invalid"],
        ["Empty"],
        ["Allocation"],
    ]


def summary_tests(task_id: str) -> str:
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


def summary_expected() -> list[list[str]]:
    return [
        ["Summary"],
        ["render_summary"],
        ["split_once"],
        ["checked_add"],
        ["checked_div"],
        ["u64::try_from", "try_from"],
        ["u32::try_from", "try_from"],
        ["Invalid"],
        ["TooMany"],
        ["Overflow"],
    ]


def frame_tests(task_id: str) -> str:
    return (
        f"use {task_id}::{{encode_frame, FrameError}};\n\n"
        f"#[test]\n"
        f"fn encodes() {{ "
        f"assert_eq!(encode_frame(b\"abc\", 8), Ok(vec![0, 0, 0, 3, b'a', b'b', b'c'])); }}\n"
        f"#[test]\n"
        f"fn rejects_limit() {{ "
        f'assert_eq!(encode_frame(b"abcdef", 3), Err(FrameError::PayloadTooLarge)); }}\n'
    )


def frame_expected() -> list[list[str]]:
    return [
        ["try_reserve"],
        ["checked_add"],
        ["u32::try_from", "try_from"],
        ["PayloadTooLarge"],
        ["Allocation"],
        ["Overflow"],
    ]


def header_tests(task_id: str) -> str:
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


def header_expected() -> list[list[str]]:
    return [
        ["HeaderError"],
        ["TooShort"],
        ["TooLarge"],
        ["get"],
        ["try_into"],
        ["from_be_bytes"],
        ["Result"],
    ]


def registration_tests(task_id: str) -> str:
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
        f'    assert_eq!(activate_user("not-an-email", 42), Err(RegistrationError::InvalidEmail));\n'
        f"}}\n\n"
        f"#[test]\n"
        f"fn rejects_missing_domain() {{\n"
        f'    assert_eq!(activate_user("ada@", 42), Err(RegistrationError::InvalidEmail));\n'
        f"}}\n"
    )


def registration_expected() -> list[list[str]]:
    return [
        ["Email"],
        ["ActiveUser"],
        ["RegistrationError"],
        ["InvalidEmail"],
        ["parse"],
        ["Result"],
        ["activated_at_epoch_ms"],
        ["enum", "struct"],
    ]


def black_hat_expected() -> list[list[str]]:
    return [
        ["contract", "parity"],
        ["test", "parity"],
        ["ignored", "commented-out", "coverage"],
        ["more than 5", "5 parameters", "parameters"],
        ["25 lines", "function over", "too long"],
        ["Functional Core", "Imperative Shell", "hidden I/O"],
        ["enum", "typestate", "state machine"],
        ["String", "bool", "newtype"],
        ["parse", "boundary"],
        ["trait", "YAGNI", "one implementer"],
        ["unwrap", "panic vector", "panic"],
        ["checked", "as", "arithmetic"],
        ["REJECT", "reject"],
    ]


def black_hat_contract(domain: str) -> str:
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


def black_hat_tests(task_id: str, domain: str) -> str:
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
        f"// Missing: typed-domain constructor tests for UserId, Amount, Region, WorkflowState, RetryLimit\n"
    )


def _append_review_hidden_io(tasks: list[TaskDict], domain: str) -> None:
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
        f"        let parts: Vec<String> = line.split(',').map(|part| part.trim().to_string()).collect();\n"
        f'        println!("loaded {{}}", parts[0]);\n'
        f"        Record {{ name: parts[0].clone(), value: parts[1].parse::<u32>().unwrap() as u16 }}\n"
        f"    }}).collect()\n"
        f"}}\n"
    )
    tasks.append(
        review_task(
            f"{family}_mixed",
            family,
            src,
            [
                ["I/O", "Actions", "read_to_string"],
                ["pure", "Calculations", "parsing"],
                ["unwrap", "panic"],
                ["String", "to_string", "allocation"],
                ["as", "try_from"],
                ["index", "bounds", "get", "split_once"],
                ["typed error", "Result"],
                ["try_reserve", "bounded"],
            ],
        )
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
        f"{{ name: fields[0].to_string(), value: fields[1].parse::<usize>().unwrap() as u16 }});\n"
        f"    }}\n"
        f"    records\n"
        f"}}\n"
    )
    tasks.append(
        review_task(
            f"{family}_precollect_frame",
            family,
            src_variant,
            [
                ["I/O", "Actions", "read_to_string"],
                ["pure", "Calculations", "parsing"],
                ["unwrap", "panic"],
                ["String", "to_string", "allocation"],
                ["as", "try_from"],
                ["index", "bounds", "get", "split_once"],
                ["typed error", "Result"],
                ["try_reserve", "bounded"],
            ],
        )
    )


def _append_review_invalid_state(tasks: list[TaskDict], domain: str) -> None:
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
    tasks.append(
        review_task(
            f"{family}_typestate",
            family,
            src,
            [
                ["enum", "typestate", "state machine"],
                ["status", "String"],
                ["bool", "lifecycle"],
                ["Option", "invalid state"],
                ["newtype", "domain"],
                ["parse", "boundary"],
            ],
        )
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
    tasks.append(
        review_task(
            f"{family}_optional_state",
            family,
            src_variant,
            [
                ["enum", "typestate", "state machine"],
                ["status", "String", "state"],
                ["bool", "lifecycle"],
                ["Option", "invalid state"],
                ["newtype", "domain"],
                ["parse", "boundary"],
            ],
        )
    )


def _append_review_perf_folklore(tasks: list[TaskDict]) -> None:
    src = (
        "pub fn classify_four(bytes: &[u8; 4]) -> Vec<&'static str> {\n"
        "    // TODO: use Rayon and SmallVec because it will be faster\n"
        '    bytes.iter().map(|byte| if *byte & 1 == 0 { "even" } else { "odd" }).collect()\n'
        "}\n"
    )
    for size in _PERF_FOLKLORE_SIZES:
        family = f"review_perf_folklore_{size}"
        tasks.append(
            review_task(
                f"{family}_rayon_smallvec",
                family,
                src,
                [
                    ["Rayon", "parallel"],
                    ["SmallVec", "smallvec"],
                    ["tiny", "fixed-size", "overhead"],
                    ["benchmark", "baseline"],
                    ["allocation", "Vec", "collect"],
                    ["array", "[&'static str; 4]"],
                ],
            )
        )


def _append_review_unsafe(tasks: list[TaskDict]) -> None:
    unsafe_cases: dict[str, str] = {
        "transmute_header": (
            "pub fn read_len(input: &[u8]) -> u32 {\n"
            "    unsafe { std::mem::transmute::<[u8; 4], u32>([input[0], input[1], input[2], input[3]]) }\n"
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
    for name, src in unsafe_cases.items():
        family = f"review_unsafe_{name}"
        tasks.append(
            review_task(
                family,
                family,
                src,
                [
                    ["unsafe", "waiver"],
                    ["bounds", "get", "chunks"],
                    ["scalar", "fallback"],
                    ["target", "feature"],
                    ["benchmark", "evidence"],
                ],
            )
        )


def _append_review_black_hat(tasks: list[TaskDict], domain: str) -> None:
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
    tasks.append(
        review_task(
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
    tasks.append(
        review_task(
            evidence_task_id,
            family,
            evidence_src,
            [
                ["proof", "test", "source", "parity"],
                ["REJECTED", "rejected"],
                ["stale", "conflicted"],
                ["zero-test", "0 tests", "zero test"],
                ["ignored", "commented-out"],
                ["panic", "panic vector"],
                ["contract", "evidence"],
                ["REJECT", "reject"],
            ],
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
                    f'// fn rejects_empty() {{ assert!(accept_{domain}("").is_err()); }}\n\n'
                    f"#[test]\n"
                    f'#[ignore = "not wired into CI"]\n'
                    f"fn accepts_non_empty() {{\n"
                    f'    assert_eq!(accept_{domain}("a"), "accepted:a".to_string());\n'
                    f"}}\n"
                ),
            },
        )
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
    tasks.append(
        review_task(
            theater_task_id,
            family,
            theater_src,
            [
                ["benchmark", "profiler", "evidence"],
                ["performance", "claim"],
                ["proof", "test", "source", "parity"],
                ["weak", "assert", "implementation detail"],
                ["trait", "YAGNI", "one implementer"],
                ["String", "bool", "newtype"],
                ["checked", "arithmetic", "overflow"],
                ["REJECT", "reject"],
            ],
            forbidden_output=_BLACK_HAT_FORBIDDEN_OUTPUT,
            doctrines=_BLACK_HAT_DOCTRINES,
            extra_files={
                "contract-spec.md": (
                    f"# {domain.title()} Fast Path Contract\n\n"
                    f"- Performance claims require benchmark and profiler evidence\n"
                    f"- Inputs must use `UserId`, `Amount`, and a workflow enum, not `String` and `bool`\n"
                    f"- Arithmetic must be checked and return typed errors\n"
                ),
                "benchmark-output.txt": "APPROVED: faster by vibes, no command output captured\n",
                "proof-review.md": "STATUS: APPROVED\nNo source-linked proof obligations were checked\n",
                "tests/behavior.rs": (
                    f"use {theater_task_id}::run_{domain}_fast_path;\n\n"
                    f"#[test]\n"
                    f"fn contains_user_id() {{\n"
                    f'    assert!(run_{domain}_fast_path("ada".to_string(), 5, true).contains("ada"));\n'
                    f"}}\n"
                ),
            },
        )
    )


def _append_review_functional(tasks: list[TaskDict], domain: str) -> None:
    family = f"review_functional_{domain}"
    src = (
        f"use std::env;\n"
        f"use std::fs;\n\n"
        f"pub fn calculate_{domain}_score(raw: &str) -> u64 {{\n"
        f'    let factor = env::var("{domain.upper()}_FACTOR").unwrap_or_else(|_| "2".to_string());\n'
        f"    let factor = factor.parse::<u64>().unwrap_or(1);\n"
        f'    println!("scoring {{}}", raw);\n'
        f'    let _ = fs::write("last-score.txt", raw);\n'
        f"    raw.split(',')\n"
        f"        .map(|part| part.trim().parse::<u64>().unwrap_or(0))\n"
        f"        .sum::<u64>() * factor\n"
        f"}}\n"
    )
    tasks.append(
        review_task(
            f"{family}_actions_in_calc",
            family,
            src,
            [
                ["Data", "Calculations", "Actions"],
                ["env", "environment"],
                ["println", "logging"],
                ["fs::write", "I/O"],
                ["hidden I/O", "side effect"],
                ["pure", "deterministic"],
                ["parse", "boundary"],
                ["typed error", "Result"],
                ["checked", "overflow"],
                ["unwrap_or", "unwrap_or_else"],
                ["silent", "default", "swallowed"],
                ["ignored", "Result", "let _"],
                ["no swallowed errors", "swallowed errors"],
            ],
            doctrines=("functional-rust", "holzman-rust"),
        )
    )


def _append_repair_csv(tasks: list[TaskDict], domain: str) -> None:
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
    tasks.append(
        repair_task(
            task_id_mixed,
            family,
            src_mixed,
            csv_tests(task_id_mixed, parse_fn),
            csv_expected(),
            _CSV_FORBIDDEN,
        )
    )

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
    tasks.append(
        repair_task(
            task_id_precollect,
            family,
            src_precollect,
            csv_tests(task_id_precollect, parse_fn),
            csv_expected(),
            _CSV_FORBIDDEN,
        )
    )

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
    tasks.append(
        repair_task(
            task_id_capacity,
            family,
            src_capacity,
            csv_tests(task_id_capacity, parse_fn),
            csv_expected(),
            _CSV_FORBIDDEN,
        )
    )


def _append_repair_summary(tasks: list[TaskDict], domain: str) -> None:
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
        "        let parts: Vec<String> = line.split(',').map(|part| part.trim().to_string()).collect();\n"
        "        let value = parts[1].parse::<u64>().unwrap();\n"
        "        total += value;\n"
        "        count += 1;\n"
        "    }\n"
        "    if count > max_rows { return Err(SummaryError::TooMany); }\n"
        '    Ok(format!("count={} total={} average={}", count as u32, total, total / count as u64))\n'
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
    tasks.append(
        repair_task(
            f"{family}_mixed",
            family,
            src_mixed,
            tests_mixed,
            [
                ["Summary"],
                ["render_summary"],
                ["split_once"],
                ["checked_add"],
                ["checked_div"],
                ["u64::try_from", "try_from"],
                ["u32::try_from", "try_from"],
                ["Invalid"],
                ["TooMany"],
                ["Overflow"],
            ],
            _SUMMARY_FORBIDDEN,
        )
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
    tasks.append(
        repair_task(
            task_id_counter,
            family,
            src_counter,
            summary_tests(task_id_counter),
            summary_expected(),
            _SUMMARY_FORBIDDEN,
        )
    )

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
    tasks.append(
        repair_task(
            task_id_radix,
            family,
            src_radix,
            summary_tests(task_id_radix),
            summary_expected(),
            _SUMMARY_FORBIDDEN,
        )
    )


def _append_repair_frame(tasks: list[TaskDict], domain: str) -> None:
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
    tasks.append(
        repair_task(
            f"{family}_mixed",
            family,
            src_mixed,
            tests_mixed,
            frame_expected(),
            _FRAME_FORBIDDEN,
        )
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
    tasks.append(
        repair_task(
            task_id_capacity,
            family,
            src_capacity,
            frame_tests(task_id_capacity),
            frame_expected(),
            _FRAME_FORBIDDEN,
        )
    )

    src_saturating = (
        "#[derive(Debug, Clone, PartialEq, Eq)]\n"
        "pub enum FrameError { PayloadTooLarge, Allocation, Overflow }\n\n"
        "pub fn encode_frame(payload: &[u8], _max_payload: usize) -> Result<Vec<u8>, FrameError> {\n"
        "    let capacity = 4usize.saturating_add(payload.len());\n"
        "    let mut out = Vec::with_capacity(capacity);\n"
        "    let len = u32::try_from(payload.len()).unwrap();\n"
        "    out.extend_from_slice(&len.to_be_bytes());\n"
        "    out.extend_from_slice(payload);\n"
        "    Ok(out)\n"
        "}\n"
    )
    task_id_saturating = f"{family}_saturating_capacity"
    tasks.append(
        repair_task(
            task_id_saturating,
            family,
            src_saturating,
            frame_tests(task_id_saturating),
            frame_expected(),
            _FRAME_FORBIDDEN,
        )
    )


def _append_repair_holzman_header(tasks: list[TaskDict], domain: str) -> None:
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
    tasks.append(
        repair_task(
            task_id,
            family,
            src,
            header_tests(task_id),
            header_expected(),
            _HEADER_FORBIDDEN,
            doctrines=("holzman-rust", "functional-rust"),
        )
    )


def _append_repair_functional_registration(tasks: list[TaskDict], domain: str) -> None:
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
    tasks.append(
        repair_task(
            task_id,
            family,
            src,
            registration_tests(task_id),
            registration_expected(),
            _REGISTRATION_FORBIDDEN,
            doctrines=("functional-rust", "holzman-rust", "black-hat-reviewer"),
        )
    )


def build_tasks() -> list[TaskDict]:
    tasks: list[TaskDict] = []
    for domain in _DOMAINS:
        _append_review_hidden_io(tasks, domain)
        _append_review_invalid_state(tasks, domain)
        _append_review_black_hat(tasks, domain)
        _append_review_functional(tasks, domain)
        _append_repair_csv(tasks, domain)
        _append_repair_summary(tasks, domain)
        _append_repair_frame(tasks, domain)
        _append_repair_holzman_header(tasks, domain)
        _append_repair_functional_registration(tasks, domain)
    _append_review_perf_folklore(tasks)
    _append_review_unsafe(tasks)
    return tasks


def split_by_family(tasks: Sequence[TaskDict], seed: int) -> dict[str, list[TaskDict]]:
    by_family: dict[str, list[TaskDict]] = {}
    for task in tasks:
        family_key = _as_str(task.get("split_family_id"), _as_str(task.get("family_id"), ""))
        by_family.setdefault(family_key, []).append(task)
    rng = random.Random(seed)
    families = sorted(by_family)
    rng.shuffle(families)
    family_order = {family: index for index, family in enumerate(families)}
    total_counts = count_items(tasks)
    targets = {split: scale_counts(total_counts, ratio) for split, ratio in _SPLIT_RATIOS.items()}
    assigned: dict[str, list[str]] = {split: [] for split in _SPLIT_RATIOS}
    counts: dict[str, CountsDict] = {split: empty_counts() for split in _SPLIT_RATIOS}
    preassigned: set[str] = set()
    black_hat_families = sorted(
        (family for family in families if family.startswith("review_black_hat_")),
        key=lambda family: family_order[family],
    )
    for split, family in zip(_SPLIT_NAMES, black_hat_families, strict=False):
        assigned[split].append(family)
        counts[split] = add_counts(counts[split], count_items(by_family[family]))
        preassigned.add(family)

    for family in sorted(families, key=lambda fam: (-len(by_family[fam]), family_order[fam])):
        if family in preassigned:
            continue
        family_count = count_items(by_family[family])
        best_split = min(
            _SPLIT_RATIOS,
            key=lambda split: (
                projected_assignment_error(split, family_count, counts, targets),
                counts[split]["total"],
                split,
            ),
        )
        assigned[best_split].append(family)
        counts[best_split] = add_counts(counts[best_split], family_count)
    return {name: [task for family in fams for task in by_family[family]] for name, fams in assigned.items()}


def empty_counts() -> CountsDict:
    return CountsDict(total=0, review=0, repair=0)


def count_items(items: Sequence[Mapping[str, object]]) -> CountsDict:
    review = sum(1 for item in items if item.get("kind") == "review")
    total = len(items)
    return CountsDict(total=total, review=review, repair=total - review)


def scale_counts(counts: CountsDict, ratio: float) -> dict[str, float]:
    return {key: _as_float(counts.get(key), 0.0) * ratio for key in _COUNT_KEYS}


def add_counts(left: CountsDict, right: CountsDict) -> CountsDict:
    return CountsDict(
        total=left["total"] + right["total"],
        review=left["review"] + right["review"],
        repair=left["repair"] + right["repair"],
    )


def projected_assignment_error(
    target_split: str,
    family_count: CountsDict,
    counts: Mapping[str, CountsDict],
    targets: Mapping[str, Mapping[str, float]],
) -> float:
    error = 0.0
    for split in _SPLIT_RATIOS:
        projected = add_counts(counts[split], family_count) if split == target_split else counts[split]
        error += relative_squared_error(projected, targets[split])
    return error


def relative_squared_error(observed: CountsDict, target: Mapping[str, float]) -> float:
    error = 0.0
    for key in _COUNT_KEYS:
        target_value = max(1.0, _as_float(target.get(key), 0.0))
        diff = _as_int(observed.get(key), 0) - target_value
        error += (diff / target_value) ** 2
    return error


def _split_family_keys(items: Sequence[TaskDict]) -> list[str]:
    return sorted(
        {_as_str(item.get("split_family_id"), _as_str(item.get("family_id"), "")) for item in items}
    )


def _family_keys(tasks: Sequence[TaskDict]) -> list[str]:
    return sorted({_as_str(task.get("family_id"), "") for task in tasks})


def _write_split_files(splits: Mapping[str, Sequence[TaskDict]], out: Path) -> None:
    for split, items in splits.items():
        split_dir = out / split
        split_dir.mkdir(parents=True, exist_ok=True)
        (split_dir / "items.json").write_text(json.dumps(list(items), indent=2) + "\n", encoding="utf-8")


def _build_manifest(
    seed: int, tasks: Sequence[TaskDict], splits: Mapping[str, Sequence[TaskDict]]
) -> ManifestDict:
    return ManifestDict(
        seed=seed,
        total_tasks=len(tasks),
        splits={split: len(items) for split, items in splits.items()},
        families=_family_keys(tasks),
        split_families={split: _split_family_keys(list(items)) for split, items in splits.items()},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate aggressive Holzman Rust SkillOpt dataset splits")
    parser.add_argument("--out", default=str(_DEFAULT_OUT))
    parser.add_argument("--seed", type=int, default=_DEFAULT_SEED)
    args = parser.parse_args()
    out = Path(args.out)
    tasks = build_tasks()
    splits = split_by_family(tasks, args.seed)
    _write_split_files(splits, out)
    manifest = _build_manifest(args.seed, tasks, splits)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
