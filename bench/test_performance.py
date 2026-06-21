from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest
from pytest_benchmark.plugin import BenchmarkFixture

from skillopt_train.rubric import Rubric
from skillopt_train.skill import Skill

from .conftest import _make_skill_dir

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