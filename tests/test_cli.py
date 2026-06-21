from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Final

import pytest

from skillopt_train import skill_train
from skillopt_train.providers import MockProvider, ScriptedTurn, make_json_response

_SAFE_ADDENDUM: Final[str] = "step 1 guidance note\n"
_DEFAULT_HARD: Final[float] = 0.8
_DEFAULT_SOFT: Final[float] = 0.5
_DEFAULT_MIXED: Final[float] = 0.65
_PASSED_TASKS: Final[int] = 1
_TASK_COUNT: Final[int] = 1


def _make_skill_bundle(skills_root: Path, name: str) -> Path:
    skill_dir = skills_root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    rubric_body = {
        "name": name,
        "forbidden_tokens": {},
        "grade_issue_keys": [],
        "grade_returncode_keys": [],
    }
    (skill_dir / "rubric.json").write_text(
        json.dumps(rubric_body, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (skill_dir / "prompt.md").write_text(
        "Custom {skill_md} {previous_addendum} {critique} {max_chars} {forbidden}\n",
        encoding="utf-8",
    )
    (skill_dir / "tasks.jsonl").write_text('{"id": "t1"}\n', encoding="utf-8")
    (skill_dir / "eval.py").write_text("# stub\n", encoding="utf-8")
    return skill_dir


def _patch_run(monkeypatch: pytest.MonkeyPatch) -> None:
    def _side_effect(args: list[str], **kwargs: object) -> object:
        run_id_idx = args.index("--run-id")
        run_id = str(args[run_id_idx + 1])
        cand_idx = args.index("--candidate-name")
        candidate_name = str(args[cand_idx + 1])
        cwd = str(kwargs.get("cwd", "."))
        run_root = Path(cwd) / "runs" / run_id
        run_root.mkdir(parents=True, exist_ok=True)
        payload: dict[str, object] = {
            "aggregates": [
                {
                    "bundle": candidate_name,
                    "hard": _DEFAULT_HARD,
                    "soft": _DEFAULT_SOFT,
                    "mixed": _DEFAULT_MIXED,
                    "passed_tasks": _PASSED_TASKS,
                    "task_count": _TASK_COUNT,
                }
            ],
            "gate": {"action": "kept"},
        }
        (run_root / "summary.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", _side_effect)


def _patch_provider(monkeypatch: pytest.MonkeyPatch) -> MockProvider:
    provider = MockProvider()
    provider.script(
        ScriptedTurn(
            match="",
            response=make_json_response(
                {"addendum": _SAFE_ADDENDUM, "reasoning": ""}
            ),
        )
    )
    monkeypatch.setattr(skill_train, "load_provider", lambda spec: provider)
    return provider


def test_cli_help_runs(capsys: pytest.CaptureFixture[str]) -> None:
    from skillopt_train.__main__ import dispatch

    with pytest.raises(SystemExit) as info:
        dispatch(("--help",))
    assert info.value.code == 0
    captured = capsys.readouterr()
    assert "run" in captured.out
    assert "list" in captured.out


def test_cli_list_subcommand_finds_skills(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    skills_root = tmp_path / "skills"
    _make_skill_bundle(skills_root, "test-skill")
    from skillopt_train.__main__ import dispatch

    code = dispatch(("list", "--skills-root", str(skills_root)))
    assert code == 0
    captured = capsys.readouterr()
    assert "test-skill" in captured.out


def test_cli_run_subcommand_invokes_skill_driven_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skills_root = tmp_path / "skills"
    _make_skill_bundle(skills_root, "test-skill")
    data_root = tmp_path / "data"
    _patch_provider(monkeypatch)
    _patch_run(monkeypatch)
    from skillopt_train.__main__ import dispatch

    code = dispatch(
        (
            "run",
            "test-skill",
            "--skills-root",
            str(skills_root),
            "--data-root",
            str(data_root),
            "--steps",
            "1",
        )
    )
    assert code == 0
    state_path = data_root / "loop_state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["step"] == 1
