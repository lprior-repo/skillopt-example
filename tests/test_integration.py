from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Final

import pytest

_REPO_ROOT: Final[Path] = Path("/home/lewis/src/skill-moo")
_SKILLS_ROOT: Final[Path] = _REPO_ROOT / "skills"
_HOLZMAN_RUST: Final[str] = "holzman-rust"
_REACT_TYPESCRIPT: Final[str] = "react-typescript"
_STEP_ARG: Final[str] = "1"
_TIMEOUT_SECONDS: Final[int] = 300
_STATE_FILENAME: Final[str] = "loop_state.json"
_LEADERBOARD_FILENAME: Final[str] = "leaderboard.jsonl"


def _uv_available() -> bool:
    return shutil.which("uv") is not None


def _apply_markers[T: Callable[..., None]](test_fn: T) -> T:
    skip_decorator = pytest.mark.skipif(
        not (_uv_available() and _SKILLS_ROOT.is_dir()),
        reason="uv not on PATH or skills/ directory missing",
    )
    integration_decorator = pytest.mark.integration
    marked: T = skip_decorator(integration_decorator(test_fn))
    return marked


def _run_cli(*args: str, data_root: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd: list[str] = [
        "uv", "run", "skillopt-train", *args,
        "--skills-root", str(_SKILLS_ROOT),
    ]
    match data_root:
        case Path() as root:
            cmd.extend(["--data-root", str(root)])
        case None:
            pass
    return subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
        timeout=_TIMEOUT_SECONDS,
    )


@_apply_markers
def test_cli_list_finds_holzman_rust() -> None:
    proc = _run_cli("list")
    assert proc.returncode == 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    assert _HOLZMAN_RUST in proc.stdout


@_apply_markers
def test_cli_list_finds_react_typescript() -> None:
    proc = _run_cli("list")
    assert proc.returncode == 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    assert _REACT_TYPESCRIPT in proc.stdout


@_apply_markers
def test_cli_run_holzman_rust_executes_one_step(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    proc = _run_cli(
        "run",
        _HOLZMAN_RUST,
        "--steps",
        _STEP_ARG,
        data_root=data_root,
    )
    assert proc.returncode == 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    assert "step" in proc.stdout
    assert "best_mixed" in proc.stdout


@_apply_markers
def test_cli_run_react_typescript_executes_one_step(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    proc = _run_cli(
        "run",
        _REACT_TYPESCRIPT,
        "--steps",
        _STEP_ARG,
        data_root=data_root,
    )
    assert proc.returncode == 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    assert "step" in proc.stdout
    assert "best_mixed" in proc.stdout


@_apply_markers
def test_cli_run_with_resume_loads_state(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    first = _run_cli(
        "run",
        _HOLZMAN_RUST,
        "--steps",
        _STEP_ARG,
        data_root=data_root,
    )
    assert first.returncode == 0, f"stdout: {first.stdout}\nstderr: {first.stderr}"
    state_path = data_root / _STATE_FILENAME
    assert state_path.is_file()
    state_before_raw: dict[str, object] = json.loads(
        state_path.read_text(encoding="utf-8")
    )
    before_step: int = 0
    match state_before_raw.get("step", 0):
        case int(v):
            before_step = v
        case _:
            pass
    second = _run_cli(
        "run",
        _HOLZMAN_RUST,
        "--steps",
        _STEP_ARG,
        "--resume",
        data_root=data_root,
    )
    assert second.returncode == 0, f"stdout: {second.stdout}\nstderr: {second.stderr}"
    state_after_raw: dict[str, object] = json.loads(
        state_path.read_text(encoding="utf-8")
    )
    match state_after_raw:
        case {"step": int(after_step)}:
            assert after_step > before_step, (
                f"resume did not advance step: before={before_step} after={after_step}"
            )
        case _:
            pytest.fail(f"state missing step field: {state_after_raw}")


@_apply_markers
def test_cli_run_creates_leaderboard(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    proc = _run_cli(
        "run",
        _HOLZMAN_RUST,
        "--steps",
        _STEP_ARG,
        data_root=data_root,
    )
    assert proc.returncode == 0, f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    leaderboard = data_root / _LEADERBOARD_FILENAME
    assert leaderboard.is_file()
    body = leaderboard.read_text(encoding="utf-8")
    lines = [line for line in body.splitlines() if line]
    assert len(lines) >= 1
