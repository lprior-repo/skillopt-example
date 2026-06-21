from __future__ import annotations

import json
from collections.abc import Mapping

from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.skillopt_train import Rubric


@given(
    name=st.text(min_size=1, max_size=16),
    description=st.text(max_size=32),
    threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    max_examples=st.integers(min_value=0, max_value=128),
)
@settings(max_examples=32, deadline=None)
def test_rubric_from_mapping_round_trip(
    name: str, description: str, threshold: float, max_examples: int
) -> None:
    payload: Mapping[str, object] = {
        "name": name,
        "description": description,
        "success_threshold_hard": threshold,
        "max_examples": max_examples,
    }
    rubric = Rubric.from_mapping(payload)
    round_tripped = Rubric.from_mapping(rubric.to_mapping())
    assert round_tripped == rubric


def test_rubric_default_invariants() -> None:
    rubric = Rubric.default()
    assert rubric.name == "default"
    assert rubric.success_threshold_hard == 1.0
    assert rubric.max_examples >= 0
    assert tuple(rubric.grade_issue_keys) == ()
    assert tuple(rubric.grade_returncode_keys) == ()
    assert dict(rubric.forbidden_tokens) == {}


@given(
    threshold=st.floats(
        min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False
    ),
    max_examples=st.integers(min_value=-3, max_value=64),
)
@settings(max_examples=32, deadline=None)
def test_rubric_threshold_falls_back_to_default_when_invalid(
    threshold: float, max_examples: int
) -> None:
    payload: Mapping[str, object] = {
        "name": "x",
        "success_threshold_hard": threshold,
        "max_examples": max_examples,
    }
    rubric = Rubric.from_mapping(payload)
    assert rubric.success_threshold_hard in {threshold, 1.0}


def test_rubric_serializes_to_json() -> None:
    rubric = Rubric.default()
    encoded = json.dumps(rubric.to_mapping())
    decoded = json.loads(encoded)
    assert decoded["name"] == rubric.name
    assert decoded["max_examples"] == rubric.max_examples
