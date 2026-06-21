from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest
from pytest_benchmark.plugin import BenchmarkFixture

from skillopt_train.rubric import Rubric
from skillopt_train.skill import Skill

from .conftest import _make_skill_dir, skills_root_large

SMALL_COUNT: Final[int] = 2
BENCH_ROUNDS: Final[int] = 20
BENCH_ITERATIONS: Final[int] = 20
TARGET_NAME: Final[str] = "skill-025"


@pytest.mark.benchmark(group="skill")
def test_bench_skill_discover_small(
    benchmark: BenchmarkFixture,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    root = tmp_path_factory.mktemp("skills_small")
    for i in range(SMALL_COUNT):
        _make_skill_dir(root, f"skill-{i:03d}")
    benchmark.pedantic(
        lambda: Skill.discover(root),
        rounds=BENCH_ROUNDS,
        iterations=BENCH_ITERATIONS,
    )


@pytest.mark.benchmark(group="skill")
def test_bench_skill_discover_large(
    benchmark: BenchmarkFixture,
    skills_root_large: Path,
) -> None:
    benchmark.pedantic(
        lambda: Skill.discover(skills_root_large),
        rounds=BENCH_ROUNDS,
        iterations=BENCH_ITERATIONS,
    )


@pytest.mark.benchmark(group="skill")
def test_bench_skill_from_path(
    benchmark: BenchmarkFixture,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    root = tmp_path_factory.mktemp("skill_single")
    _make_skill_dir(root, "alpha")
    skill_path = root / "alpha"
    benchmark.pedantic(
        lambda: Skill.from_path(skill_path),
        rounds=BENCH_ROUNDS,
        iterations=BENCH_ITERATIONS,
    )


@pytest.mark.benchmark(group="skill")
def test_bench_skill_load_prompt(
    benchmark: BenchmarkFixture,
    skills_root_large: Path,
) -> None:
    skill = Skill.from_path(skills_root_large / "skill-000")
    benchmark.pedantic(
        skill.load_prompt,
        rounds=BENCH_ROUNDS,
        iterations=BENCH_ITERATIONS,
    )


@pytest.mark.benchmark(group="rubric")
def test_bench_rubric_from_path(
    benchmark: BenchmarkFixture,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    root = tmp_path_factory.mktemp("rubric_single")
    _make_skill_dir(root, "alpha")
    rubric_path = root / "alpha" / "rubric.json"
    benchmark.pedantic(
        lambda: Rubric.from_path(rubric_path),
        rounds=BENCH_ROUNDS,
        iterations=BENCH_ITERATIONS,
    )


@pytest.mark.benchmark(group="rubric")
def test_bench_rubric_from_mapping(benchmark: BenchmarkFixture) -> None:
    data: dict[str, object] = {
        "name": "alpha",
        "description": "bench rubric",
        "forbidden_tokens": {"unsafe": "forbidden:unsafe"},
        "grade_issue_keys": ["json_errors"],
        "grade_returncode_keys": ["cargo_fmt_returncode"],
        "success_threshold_hard": 1.0,
        "max_examples": 5,
    }
    benchmark.pedantic(
        Rubric.from_mapping,
        args=(data,),
        rounds=BENCH_ROUNDS,
        iterations=BENCH_ITERATIONS,
    )


@pytest.mark.benchmark(group="rubric")
def test_bench_rubric_to_mapping(benchmark: BenchmarkFixture) -> None:
    rubric = Rubric.default()
    benchmark.pedantic(
        rubric.to_mapping,
        rounds=BENCH_ROUNDS,
        iterations=BENCH_ITERATIONS,
    )


@pytest.mark.benchmark(group="skill")
def test_bench_skill_find(
    benchmark: BenchmarkFixture,
    skills_root_large: Path,
) -> None:
    benchmark.pedantic(
        lambda: Skill.find(skills_root_large, TARGET_NAME),
        rounds=BENCH_ROUNDS,
        iterations=BENCH_ITERATIONS,
    )