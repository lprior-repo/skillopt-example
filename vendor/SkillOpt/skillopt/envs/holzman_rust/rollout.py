from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from pygments import lex
from pygments.lexers import RustLexer
from pygments.token import Comment, String

FORBIDDEN_SOURCE_PATTERNS = [
    ("unsafe", re.compile(r"\bunsafe\b")),
    ("unwrap", re.compile(r"\.unwrap\s*\(")),
    ("unwrap_or", re.compile(r"\.unwrap_or(?:_else|_default)?\s*\(")),
    ("expect", re.compile(r"\.expect\s*\(")),
    ("panic", re.compile(r"\bpanic!\s*\(")),
    ("todo", re.compile(r"\btodo!\s*\(")),
    ("unimplemented", re.compile(r"\bunimplemented!\s*\(")),
    ("unreachable", re.compile(r"\bunreachable!\s*\(")),
    ("assert", re.compile(r"\bassert(?:_eq|_ne)?!\s*\(")),
    ("ignored_result", re.compile(r"let\s+_\s*=\s*[^;]*\b(Result|fs::|write|send|flush|try_reserve)")),
    ("stdout_print", re.compile(r"\bprintln!\s*\(")),
    ("stderr_print", re.compile(r"\beprintln!\s*\(")),
    ("hidden_fs", re.compile(r"\b(std::fs|fs::)")),
    ("hidden_env", re.compile(r"\b(std::env|env::var)")),
    ("hidden_process", re.compile(r"\b(std::process|Command::new)")),
    ("hidden_network", re.compile(r"\b(std::net|TcpStream|UdpSocket)")),
    ("hidden_time", re.compile(r"\b(SystemTime|Instant::now|thread::sleep)")),
]

ABSOLUTE_PATH_PATTERN = re.compile(r"(^|[\s\"'([{=,])/{1,}[^\s\"'\])},]+")
FILE_URI_PATH_PATTERN = re.compile(r"\bfile:/+", re.IGNORECASE)
RUST_LEXER = RustLexer()


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_fixture(item: dict, workdir: Path) -> None:
    files = item.get("files") or {}
    if not isinstance(files, dict):
        raise ValueError(f"task {item.get('id')} files must be an object")
    for rel, content in files.items():
        path = workdir / str(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")


def file_hashes(root: Path, files: dict[str, str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for rel in files:
        path = root / rel
        if path.exists() and path.is_file():
            hashes[rel] = sha256_text(path.read_text(encoding="utf-8", errors="replace"))
    return hashes


def tree_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    if not root.exists():
        return hashes
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            hashes[rel] = sha256_text(path.read_text(encoding="utf-8", errors="replace"))
    return hashes


def tree_diff(before: dict[str, str], after: dict[str, str]) -> dict[str, list[str]]:
    before_keys = set(before)
    after_keys = set(after)
    return {
        "added": sorted(after_keys - before_keys),
        "removed": sorted(before_keys - after_keys),
        "changed": sorted(path for path in before_keys & after_keys if before[path] != after[path]),
    }


def run_command(args: list[str], workdir: Path, timeout: int, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        proc = subprocess.run(
            args,
            cwd=str(workdir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=env,
        )
        return {
            "command": args,
            "cwd": str(workdir),
            "started_at": started,
            "returncode": proc.returncode,
            "stdout": _text(proc.stdout),
            "stderr": _text(proc.stderr),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": args,
            "cwd": str(workdir),
            "started_at": started,
            "returncode": 124,
            "stdout": _text(exc.stdout),
            "stderr": _text(exc.stderr) or "timeout",
            "timed_out": True,
        }


def opencode_env(workdir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["OPENCODE_DISABLE_EXTERNAL_SKILLS"] = "1"
    env["OPENCODE_DISABLE_CLAUDE_CODE_SKILLS"] = "1"
    env["OPENCODE_DISABLE_DEFAULT_PLUGINS"] = "1"
    env["OPENCODE_CONFIG_CONTENT"] = json.dumps({"lsp": False})
    target_hash = hashlib.sha256(str(workdir).encode("utf-8")).hexdigest()[:16]
    env["CARGO_TARGET_DIR"] = str(Path("/tmp/opencode/holzman-skillopt-targets") / target_hash)
    state_root = Path("/tmp/opencode/holzman-skillopt-opencode") / target_hash
    for name, child in [
        ("XDG_DATA_HOME", "data"),
        ("XDG_STATE_HOME", "state"),
        ("XDG_CACHE_HOME", "cache"),
    ]:
        path = state_root / child
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    return env


def materialize_skill(skill_content: str, skill_dir: Path, references_dir: Path | None) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
    target_refs = skill_dir / "references"
    target_refs.mkdir(parents=True, exist_ok=True)
    if references_dir and references_dir.exists():
        for source in sorted(item for item in references_dir.rglob("*") if item.is_file()):
            rel = source.relative_to(references_dir)
            target = target_refs / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def review_prompt(item: dict, skill_dir: Path, workdir: Path, output_path: Path) -> str:
    return """
You are running a Holzman Rust SkillOpt rollout. Do not use global skills or memory.

Active skill bundle:
- SKILL.md: .skill/holzman-rust/SKILL.md
- references: .skill/holzman-rust/references

Task crate path: .
Required output path: review-output.json

Review exactly the task crate for Holzman + Functional Rust violations.

Rules:
- Read the active skill bundle and applicable references before reviewing.
- Review only the task crate path above.
- Do not inspect parent directories, sibling tasks, eval manifests, candidates, or reports.
- Do not edit Cargo.toml, source, tests, or production files.
- Do not run cargo commands for review tasks.
- You may write only the required output path.
- In JSON fields, report paths relative to the task crate or active skill bundle; do not write any absolute path such as /tmp/x or /dev/null.
- Findings must include severity, rule, file, line, problem, failure_mode, and fix.
- Include missing benchmark/profiler/allocation/second-ring/command evidence as findings when relevant.

Write valid JSON to the required output path:
{
  "status": "reviewed",
  "reference_files_read": ["..."],
  "findings": [{"severity":"BLOCKER","rule":"...","file":"src/lib.rs","line":1,"problem":"...","failure_mode":"...","fix":"..."}],
  "missing_evidence": [],
  "residual_risk": "..."
}
""".strip()


def repair_prompt(item: dict, skill_dir: Path, workdir: Path, output_path: Path) -> str:
    return """
You are running a Holzman Rust SkillOpt repair rollout. Do not use global skills or memory.

Active skill bundle:
- SKILL.md: .skill/holzman-rust/SKILL.md
- references: .skill/holzman-rust/references

Task crate path: .
Required output path: repair-output.json

Repair exactly the task crate.

Rules:
- Read the active skill bundle and applicable references before editing.
- Repair only the task crate path above.
- Read Cargo.toml, production source, and tests before editing.
- Do not edit tests. Tests are the behavior contract.
- Do not edit Cargo.toml unless compilation is otherwise impossible.
- Make the smallest production-source change that satisfies tests and Holzman + Functional Rust constraints.
- Push logic into pure core and keep I/O/rendering/actions in the shell only when the tests/failure mode require it.
- Remove production unsafe/unwrap/expect/panic/todo/unimplemented/unreachable/assert macros, unchecked indexing, unchecked arithmetic, and lossy as conversions.
- Run cargo fmt after editing, then cargo test.
- Write valid JSON to the required output path after commands run.
- In JSON fields, report paths relative to the task crate or active skill bundle; do not write any absolute path such as /tmp/x or /dev/null.

Required JSON shape:
{
  "status": "repaired",
  "reference_files_read": ["..."],
  "changed_files": ["src/lib.rs"],
  "commands": [{"command":"cargo test","status":"passed"}],
  "rules_satisfied": ["..."],
  "skipped_gates": [],
  "residual_risk": "..."
}
""".strip()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_json_object(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, ["missing_json"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"json_decode_error={exc}"]
    if not isinstance(payload, dict):
        return None, ["json_not_object"]
    return payload, []


def validate_review_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    payload, errors = parse_json_object(path)
    if payload is None:
        return None, errors
    if payload.get("status") != "reviewed":
        errors.append("status_not_reviewed")
    refs = payload.get("reference_files_read")
    if not isinstance(refs, list) or not refs:
        errors.append("missing_reference_files_read")
    findings = payload.get("findings")
    if not isinstance(findings, list) or not findings:
        errors.append("missing_findings")
    else:
        required = {"severity", "rule", "file", "line", "problem", "failure_mode", "fix"}
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                errors.append(f"finding_{index}_not_object")
                continue
            missing = sorted(required - set(finding))
            if missing:
                errors.append(f"finding_{index}_missing={','.join(missing)}")
            file_value = str(finding.get("file", ""))
            if file_value.startswith("/") or ".." in Path(file_value).parts:
                errors.append(f"finding_{index}_bad_file={file_value}")
    return payload, errors


def validate_repair_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    payload, errors = parse_json_object(path)
    if payload is None:
        return None, errors
    if payload.get("status") != "repaired":
        errors.append("status_not_repaired")
    for key in ["reference_files_read", "changed_files", "commands", "rules_satisfied", "skipped_gates"]:
        if not isinstance(payload.get(key), list):
            errors.append(f"{key}_not_list")
    refs = payload.get("reference_files_read")
    if not isinstance(refs, list) or not refs:
        errors.append("missing_reference_files_read")
    commands = payload.get("commands")
    if isinstance(commands, list):
        for index, command in enumerate(commands):
            if not isinstance(command, dict):
                errors.append(f"command_{index}_not_object")
                continue
            if not isinstance(command.get("command"), str) or not command.get("command"):
                errors.append(f"command_{index}_missing_command")
            if not isinstance(command.get("status"), str) or not command.get("status"):
                errors.append(f"command_{index}_missing_status")
    skipped = payload.get("skipped_gates")
    if isinstance(skipped, list) and skipped:
        errors.append("skipped_gates_nonempty")
    return payload, errors


def match_groups(text: str, groups: list[list[str]]) -> tuple[int, list[list[str]]]:
    lower = text.lower()
    matched = 0
    missing: list[list[str]] = []
    for group in groups:
        if any(str(term).lower() in lower for term in group):
            matched += 1
        else:
            missing.append(group)
    return matched, missing


def execution_clean(opencode: dict[str, Any]) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if int(opencode.get("returncode", 1)) != 0:
        problems.append(f"opencode_returncode={opencode.get('returncode')}")
    if opencode.get("timed_out"):
        problems.append("opencode_timeout")
    combined = str(opencode.get("stdout", "")) + "\n" + str(opencode.get("stderr", ""))
    if "Invalid Tool" in combined:
        problems.append("invalid_tool_call")
    for term in [
        "/home/lewis/src/skill-moo/evals",
        "evals/holzman-rust/tasks.json",
        "/home/lewis/src/skill-moo/candidates",
        "/home/lewis/src/skill-moo/reports",
    ]:
        if term in combined:
            problems.append(f"leaked_path={term}")
    return not problems, problems


def source_text(workdir: Path) -> str:
    src = workdir / "src"
    if not src.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in sorted(src.rglob("*.rs")))


def rust_code_token_text(text: str) -> str:
    tokens: list[str] = []
    for token_type, value in lex(text, RUST_LEXER):
        if token_type in Comment or token_type in String:
            tokens.append("\n" * value.count("\n"))
        else:
            tokens.append(value)
    return "".join(tokens)


def forbidden_matches(text: str) -> list[str]:
    return [name for name, pattern in FORBIDDEN_SOURCE_PATTERNS if pattern.search(text)]


def item_forbidden_matches(text: str, patterns: list[Any]) -> list[str]:
    matches: list[str] = []
    for index, raw in enumerate(patterns):
        if isinstance(raw, dict):
            name = str(raw.get("name") or f"forbidden_{index}")
            pattern = str(raw.get("pattern") or "")
        else:
            name = str(raw)
            pattern = str(raw)
        if not pattern:
            continue
        try:
            found = re.search(pattern, text, flags=re.MULTILINE) is not None
        except re.error:
            found = pattern in text
        if found:
            matches.append(name)
    return matches


def output_policy_errors(payload: Any) -> list[str]:
    errors: list[str] = []

    def is_path_field(path: str) -> bool:
        return (
            path.startswith("reference_files_read[")
            or path.startswith("changed_files[")
            or path.endswith(".file")
            or path == "file"
        )

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")
        elif isinstance(value, str) and (ABSOLUTE_PATH_PATTERN.search(value) or FILE_URI_PATH_PATTERN.search(value)):
            errors.append(f"absolute_path_in_output={path}")
        elif isinstance(value, str) and is_path_field(path) and (value.startswith("/") or ".." in Path(value).parts):
            errors.append(f"bad_relative_path_in_output={path}")

    if payload is not None:
        visit(payload, "")
    return sorted(set(errors))


def review_obligation_text(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return ""
    fields = ["severity", "rule", "file", "problem", "failure_mode", "fix"]
    chunks: list[str] = []
    for finding in findings:
        if isinstance(finding, dict):
            chunks.extend(str(finding.get(field, "")) for field in fields)
    return "\n".join(chunks)


def grade_review(item: dict, workdir: Path, before_tree: dict[str, str], opencode: dict[str, Any]) -> dict[str, Any]:
    payload, json_errors = validate_review_json(workdir / "review-output.json")
    combined = json.dumps(payload, sort_keys=True) if payload is not None else ""
    matched, missing = match_groups(review_obligation_text(payload), item.get("expected_output_groups") or [])
    forbidden_output = item_forbidden_matches(combined, item.get("forbidden_output_patterns") or [])
    output_errors = output_policy_errors(payload)
    diff = tree_diff(before_tree, tree_hashes(workdir))
    allowed_added = {"review-output.json"}
    mutation_errors = [f"added:{p}" for p in diff["added"] if p not in allowed_added]
    mutation_errors += [f"removed:{p}" for p in diff["removed"]]
    mutation_errors += [f"changed:{p}" for p in diff["changed"]]
    clean, execution_errors = execution_clean(opencode)
    group_total = max(1, len(item.get("expected_output_groups") or []))
    group_score = matched / group_total
    json_valid = payload is not None and not json_errors
    soft = group_score if json_valid else 0.0
    if mutation_errors:
        soft *= 0.5
    if not clean:
        soft *= 0.5
    if forbidden_output:
        soft *= 0.5
    if output_errors:
        soft *= 0.5
    hard = (
        group_score >= 1.0
        and json_valid
        and not mutation_errors
        and clean
        and not forbidden_output
        and not output_errors
    )
    return {
        "hard": 1.0 if hard else 0.0,
        "soft": soft,
        "failures": missing
        + [[err] for err in json_errors + mutation_errors + execution_errors + forbidden_output + output_errors],
        "json_valid": json_valid,
        "matched_groups": matched,
        "total_groups": group_total,
        "missing_groups": missing,
        "forbidden_output_matches": forbidden_output,
        "output_policy_errors": output_errors,
        "execution_errors": execution_errors,
        "mutation_errors": mutation_errors,
    }


def grade_repair(
    item: dict,
    workdir: Path,
    artifact_dir: Path,
    protected_hashes: dict[str, str],
    initial: dict[str, Any] | None,
    opencode: dict[str, Any],
    cargo_timeout: int,
) -> dict[str, Any]:
    env = opencode_env(workdir)
    fmt = run_command(["cargo", "fmt", "--check"], workdir, cargo_timeout, env=env)
    clippy = run_command(
        [
            "cargo",
            "clippy",
            "--lib",
            "--all-features",
            "--",
            "-D",
            "warnings",
            "-D",
            "unsafe_code",
            "-D",
            "clippy::unwrap_used",
            "-D",
            "clippy::expect_used",
            "-D",
            "clippy::panic",
            "-D",
            "clippy::panic_in_result_fn",
            "-D",
            "clippy::todo",
            "-D",
            "clippy::unimplemented",
            "-D",
            "clippy::dbg_macro",
            "-D",
            "clippy::indexing_slicing",
            "-D",
            "clippy::string_slice",
            "-D",
            "clippy::get_unwrap",
            "-D",
            "clippy::arithmetic_side_effects",
            "-D",
            "clippy::as_conversions",
            "-D",
            "clippy::let_underscore_must_use",
        ],
        workdir,
        cargo_timeout,
        env=env,
    )
    test = run_command(["cargo", "test"], workdir, cargo_timeout, env=env)
    for name, result in [("cargo-fmt", fmt), ("cargo-clippy", clippy), ("cargo-test", test)]:
        (artifact_dir / f"grader-{name}.stdout.txt").write_text(result["stdout"], encoding="utf-8")
        (artifact_dir / f"grader-{name}.stderr.txt").write_text(result["stderr"], encoding="utf-8")

    payload, json_errors = validate_repair_json(workdir / "repair-output.json")
    src_text = source_text(workdir)
    obligation_text = rust_code_token_text(src_text)
    output_text = json.dumps(payload, sort_keys=True) if payload is not None else ""
    matched, missing = match_groups(obligation_text, item.get("expected_source_groups") or [])
    item_forbidden = item_forbidden_matches(obligation_text, item.get("forbidden_source_patterns") or [])
    forbidden_output = item_forbidden_matches(output_text, item.get("forbidden_output_patterns") or [])
    output_errors = output_policy_errors(payload)
    protected_after = file_hashes(workdir, {path: "" for path in protected_hashes})
    protected_changed = sorted(
        path for path in protected_hashes if protected_hashes.get(path) != protected_after.get(path)
    )
    forbidden = forbidden_matches(obligation_text)
    clean, execution_errors = execution_clean(opencode)
    initial_failed = initial is not None and int(initial.get("returncode", 0)) != 0
    fmt_passed = fmt["returncode"] == 0
    clippy_passed = clippy["returncode"] == 0
    tests_passed = test["returncode"] == 0
    json_valid = payload is not None and not json_errors
    group_total = max(1, len(item.get("expected_source_groups") or []))
    group_score = matched / group_total
    soft = 0.0
    if tests_passed:
        soft += 0.30
    if clippy_passed:
        soft += 0.20
    if fmt_passed:
        soft += 0.10
    if not forbidden:
        soft += 0.10
    if not protected_changed:
        soft += 0.05
    if json_valid:
        soft += 0.05
    if clean:
        soft += 0.05
    if initial_failed:
        soft += 0.05
    soft += 0.10 * group_score
    if item_forbidden:
        soft *= 0.5
    if forbidden_output:
        soft *= 0.5
    if output_errors:
        soft *= 0.5
    hard = (
        tests_passed
        and clippy_passed
        and fmt_passed
        and not forbidden
        and not item_forbidden
        and not forbidden_output
        and not output_errors
        and not protected_changed
        and json_valid
        and clean
        and initial_failed
        and group_score >= 1.0
    )
    failures = missing + [
        [err]
        for err in json_errors
        + protected_changed
        + forbidden
        + item_forbidden
        + forbidden_output
        + output_errors
        + execution_errors
    ]
    return {
        "hard": 1.0 if hard else 0.0,
        "soft": min(1.0, soft),
        "failures": failures,
        "json_valid": json_valid,
        "fmt_passed": fmt_passed,
        "clippy_passed": clippy_passed,
        "tests_passed": tests_passed,
        "protected_changed": protected_changed,
        "forbidden_matches": forbidden,
        "item_forbidden_matches": item_forbidden,
        "forbidden_output_matches": forbidden_output,
        "output_policy_errors": output_errors,
        "matched_groups": matched,
        "total_groups": group_total,
        "missing_groups": missing,
        "execution_errors": execution_errors,
    }


def copy_artifacts(workdir: Path, artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for rel in ["Cargo.toml", "Cargo.lock", "review-output.json", "repair-output.json"]:
        source = workdir / rel
        if source.exists() and source.is_file():
            target = artifact_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for rel in ["src", "tests"]:
        source = workdir / rel
        if source.exists() and source.is_dir():
            target = artifact_dir / rel
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)


def write_conversation(
    prediction_dir: Path, item: dict, prompt: str, stdout: str, stderr: str, grade: dict[str, Any]
) -> None:
    prediction_dir.mkdir(parents=True, exist_ok=True)
    conversation = [
        {"role": "user", "content": prompt},
        {"role": "agent", "content": stdout[-12000:]},
        {"role": "verification", "content": json.dumps({"stderr_tail": stderr[-4000:], "grade": grade}, indent=2)},
    ]
    (prediction_dir / "conversation.json").write_text(json.dumps(conversation, indent=2) + "\n", encoding="utf-8")
    (prediction_dir / "target_user_prompt.txt").write_text(prompt, encoding="utf-8")


def run_item(
    item: dict,
    *,
    skill_content: str,
    out_root: Path,
    sandbox_root: Path,
    references_dir: Path | None,
    review_model: str,
    repair_model: str,
    opencode_variant: str,
    opencode_show_thinking: bool,
    opencode_timeout: int,
    cargo_timeout: int,
) -> dict[str, Any]:
    item_id = str(item["id"])
    kind = str(item.get("kind") or item.get("task_type") or "review")
    artifact_dir = out_root / "predictions" / item_id
    workdir = sandbox_root / item_id
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)
    if workdir.exists():
        shutil.rmtree(workdir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    write_fixture(item, workdir)
    skill_dir = workdir / ".skill" / "holzman-rust"
    materialize_skill(skill_content, skill_dir, references_dir)
    fixture_fmt = run_command(["cargo", "fmt"], workdir, cargo_timeout, env=opencode_env(workdir))
    (artifact_dir / "fixture-cargo-fmt.stdout.txt").write_text(fixture_fmt["stdout"], encoding="utf-8")
    (artifact_dir / "fixture-cargo-fmt.stderr.txt").write_text(fixture_fmt["stderr"], encoding="utf-8")
    before_tree = tree_hashes(workdir)
    files = item.get("files") or {}
    protected = {
        path: content for path, content in files.items() if path == "Cargo.toml" or str(path).startswith("tests/")
    }
    protected_hashes = file_hashes(workdir, protected)

    initial = None
    if kind == "repair":
        initial = run_command(["cargo", "test"], workdir, cargo_timeout, env=opencode_env(workdir))
        (artifact_dir / "initial-cargo-test.stdout.txt").write_text(initial["stdout"], encoding="utf-8")
        (artifact_dir / "initial-cargo-test.stderr.txt").write_text(initial["stderr"], encoding="utf-8")

    output_name = "review-output.json" if kind == "review" else "repair-output.json"
    output_path = workdir / output_name
    prompt = (
        review_prompt(item, skill_dir, workdir, output_path)
        if kind == "review"
        else repair_prompt(item, skill_dir, workdir, output_path)
    )
    (artifact_dir / "eval-prompt.md").write_text(prompt, encoding="utf-8")
    model = review_model if kind == "review" else repair_model
    args = [
        "opencode",
        "run",
        "--pure",
        "--dir",
        str(workdir),
        "--agent",
        "build",
        "--dangerously-skip-permissions",
    ]
    if model:
        args.extend(["--model", model])
    if opencode_variant:
        args.extend(["--variant", opencode_variant])
    if opencode_show_thinking:
        args.append("--thinking")
    args.extend(["--title", f"skillopt-holzman-{item_id}", prompt])
    opencode = run_command(args, workdir, opencode_timeout, env=opencode_env(workdir))
    if int(opencode.get("returncode", 0)) != 0:
        (artifact_dir / "opencode-attempt1.stdout.txt").write_text(opencode["stdout"], encoding="utf-8")
        (artifact_dir / "opencode-attempt1.stderr.txt").write_text(opencode["stderr"], encoding="utf-8")
        opencode = run_command(args, workdir, opencode_timeout, env=opencode_env(workdir))
    (artifact_dir / "opencode.stdout.txt").write_text(opencode["stdout"], encoding="utf-8")
    (artifact_dir / "opencode.stderr.txt").write_text(opencode["stderr"], encoding="utf-8")
    if kind == "review":
        grade = grade_review(item, workdir, before_tree, opencode)
    else:
        grade = grade_repair(item, workdir, artifact_dir, protected_hashes, initial, opencode, cargo_timeout)
    copy_artifacts(workdir, artifact_dir)
    write_conversation(artifact_dir, item, prompt, opencode["stdout"], opencode["stderr"], grade)
    result = {
        "id": item_id,
        "hard": int(grade["hard"] >= 1.0),
        "soft": float(grade["soft"]),
        "task_type": kind,
        "task_description": str(item.get("description") or item_id),
        "fail_reason": "; ".join("/".join(map(str, group)) for group in grade.get("failures") or [])[:1000],
        "target_user_prompt": prompt,
        "predicted_answer": read_text(workdir / output_name),
        "n_turns": 1,
        "model": model,
        "opencode_variant": opencode_variant,
        "opencode_show_thinking": opencode_show_thinking,
        "artifact_dir": str(artifact_dir),
        "sandbox_workdir": str(workdir),
        "grade": grade,
    }
    (artifact_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def interleave_by_kind(items: list[dict]) -> list[dict]:
    """Keep review and repair model endpoints fed with a two-worker pool."""
    reviews: list[dict] = []
    repairs: list[dict] = []
    others: list[dict] = []
    for item in items:
        kind = str(item.get("kind") or item.get("task_type") or "review")
        if kind == "review":
            reviews.append(item)
        elif kind == "repair":
            repairs.append(item)
        else:
            others.append(item)

    scheduled: list[dict] = []
    max_len = max(len(reviews), len(repairs), len(others), 0)
    for index in range(max_len):
        if index < len(reviews):
            scheduled.append(reviews[index])
        if index < len(repairs):
            scheduled.append(repairs[index])
        if index < len(others):
            scheduled.append(others[index])
    return scheduled


def run_batch(
    *,
    items: list[dict],
    out_root: str,
    skill_content: str,
    references_dir: str,
    review_model: str,
    repair_model: str,
    opencode_variant: str,
    opencode_show_thinking: bool,
    workers: int,
    opencode_timeout: int,
    cargo_timeout: int,
    sandbox_root: str,
) -> list[dict]:
    out_path = Path(out_root)
    out_path.mkdir(parents=True, exist_ok=True)
    sandbox = Path(sandbox_root) / sha256_text(str(out_path))[:16]
    sandbox.mkdir(parents=True, exist_ok=True)
    refs = Path(references_dir) if references_dir else None
    results: list[dict] = []
    scheduled_items = interleave_by_kind(items)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [
            executor.submit(
                run_item,
                item,
                skill_content=skill_content,
                out_root=out_path,
                sandbox_root=sandbox,
                references_dir=refs,
                review_model=review_model,
                repair_model=repair_model,
                opencode_variant=opencode_variant,
                opencode_show_thinking=opencode_show_thinking,
                opencode_timeout=opencode_timeout,
                cargo_timeout=cargo_timeout,
            )
            for item in scheduled_items
        ]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: str(row.get("id")))
    (out_path / "rollout_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results
