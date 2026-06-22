"""Pure configuration parser for the mutmut shim.

This module owns every value-in / value-out transformation the shim
performs on ``pyproject.toml`` and ``setup.cfg``: text parsing,
legacy-key normalization, type coercion, and CLI argument filtering.
Side effects (filesystem reads, dynamic imports, process invocation,
``sys.exit``) belong to :mod:`mutmut_runner`, which is the matching
thin shell.

Every public pure function carries ``@beartype`` plus
``@icontract.require`` / ``@icontract.ensure`` so CrossHair can prove
the contracts.
"""

from __future__ import annotations

import re
import warnings
from collections.abc import Mapping, Sequence
from configparser import ConfigParser
from dataclasses import dataclass
from tomllib import loads as _toml_loads
from typing import Final

import icontract
from beartype import beartype
from expression import Error, Ok, Result
from pyrsistent import PMap, PVector, pmap, pvector

from scripts.errors import DomainError

__all__ = [
    "ALIAS",
    "KNOWN_FLAGS",
    "LEGACY_KEYS",
    "STRIP_FLAGS",
    "MutmutConfig",
    "MutmutConfigError",
    "build_mutmut_config",
    "coerce_bool",
    "coerce_float",
    "coerce_int",
    "coerce_str_list",
    "filter_args",
    "mutmut_config_error",
    "normalize_section",
    "parse_ini_section",
    "parse_mutmut_config",
    "parse_toml_mutmut_section",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class MutmutConfigError(DomainError):
    """Errors raised when assembling or validating the mutmut shim config."""

    code: str = "mutmut_config_error"


def mutmut_config_error(message: str) -> MutmutConfigError:
    """Build a :class:`MutmutConfigError` for the given ``message``."""
    return MutmutConfigError(message=message)


LEGACY_KEYS: Final[frozenset[str]] = frozenset({"paths_to_mutate", "tests_dir"})
ALIAS: Final[Mapping[str, str]] = {
    "paths_to_mutate": "source_paths",
    "tests_dir": "pytest_add_cli_args_test_selection",
}
KNOWN_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "--max-children",
        "--all",
        "--show-killed",
        "--help",
        "--version",
    }
)
STRIP_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "--source-paths",
        "--no-progress",
        "--no-color",
        "--runner",
    }
)


_INT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*[+-]?\d+\s*")
_FLOAT_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*[+-]?\d+(?:\.\d+)?\s*")
_TRUE_TOKENS: Final[frozenset[str]] = frozenset({"1", "t", "true", "yes"})


@dataclass(frozen=True, slots=True, kw_only=True)
class MutmutConfig:
    """Validated, defaulted mutmut configuration.

    All sequence fields carry :class:`PVector` values for structural
    sharing. Paths are kept as strings here; the shell converts them
    to :class:`pathlib.Path` when constructing the external
    ``mutmut.configuration.Config``.
    """

    only_mutate: PVector[str]
    do_not_mutate: PVector[str]
    do_not_mutate_patterns: PVector[str]
    also_copy: PVector[str]
    max_stack_depth: int
    debug: bool
    mutate_only_covered_lines: bool
    source_paths: PVector[str]
    pytest_add_cli_args: PVector[str]
    pytest_add_cli_args_test_selection: PVector[str]
    timeout_multiplier: float
    timeout_constant: float
    type_check_command: PVector[str]
    use_setproctitle: bool


def _always_true() -> bool:
    """Trivially-true contract used when no precondition is meaningful."""
    return True


def _is_pmap_str_str(result: object) -> bool:
    """Guarantee the result is a :class:`PMap` of strings to strings."""
    return isinstance(result, PMap)


def _is_pmap_str_object(result: object) -> bool:
    """Guarantee the result is a :class:`PMap` of strings to objects."""
    return isinstance(result, PMap)


def _is_pvector_str(result: object) -> bool:
    """Guarantee the result is a :class:`PVector` of strings."""
    return isinstance(result, PVector)


def _ok_or_mutmut_error(result: object) -> bool:
    """Guarantee ``Result`` carries either :class:`MutmutConfig` or :class:`MutmutConfigError`."""
    if result.is_ok():
        return isinstance(result.ok, MutmutConfig)
    return isinstance(result.error, MutmutConfigError)


def _coerce_int_pre(value: object) -> bool:
    """Allow ``None``, booleans, numbers, and strings as inputs."""
    return value is None or isinstance(value, (bool, int, float, str))


@beartype
@icontract.require(_coerce_int_pre)
@icontract.ensure(lambda result: isinstance(result, int))
def coerce_int(value: object, default: int) -> int:
    """Coerce ``value`` to ``int`` if possible, else return ``default``.

    Strings are accepted only when they fully match :data:`_INT_PATTERN`
    so the conversion never raises.
    """
    match value:
        case bool():
            return int(value)
        case int():
            return value
        case float() if float(value).is_integer():
            return int(value)
        case str() if _INT_PATTERN.fullmatch(value):
            return int(value)
        case _:
            pass
    return default


def _coerce_float_pre(value: object) -> bool:
    """Allow ``None``, booleans, numbers, and strings as inputs."""
    return value is None or isinstance(value, (bool, int, float, str))


@beartype
@icontract.require(_coerce_float_pre)
@icontract.ensure(lambda result: isinstance(result, float))
def coerce_float(value: object, default: float) -> float:
    """Coerce ``value`` to ``float`` if possible, else return ``default``.

    Strings are accepted only when they fully match :data:`_FLOAT_PATTERN`
    so the conversion never raises.
    """
    match value:
        case bool() | int() | float():
            return float(value)
        case str() if _FLOAT_PATTERN.fullmatch(value):
            return float(value)
        case _:
            pass
    return default


def _coerce_bool_pre(value: object) -> bool:
    """Allow ``None``, booleans, and strings as inputs."""
    return value is None or isinstance(value, (bool, str))


@beartype
@icontract.require(_coerce_bool_pre)
@icontract.ensure(lambda result: isinstance(result, bool))
def coerce_bool(value: object, default: bool) -> bool:
    """Coerce ``value`` to ``bool`` if possible, else return ``default``."""
    match value:
        case bool():
            return value
        case str():
            return value.lower() in _TRUE_TOKENS
        case _:
            pass
    return default


@beartype
def coerce_str_list(value: object) -> PVector[str]:
    """Coerce ``value`` to a :class:`PVector` of strings.

    ``None`` becomes an empty vector; a list or tuple is mapped
    element-wise; anything else is wrapped in a single-element vector.
    """
    match value:
        case None:
            return pvector()
        case list() | tuple():
            return pvector(str(item) for item in value)
        case _:
            return pvector([str(value)])


def _ini_section_pre(text: str, section: str) -> bool:
    """Require a non-empty ``section`` to read."""
    return isinstance(text, str) and isinstance(section, str) and bool(section)


@beartype
@icontract.require(_ini_section_pre)
@icontract.ensure(_is_pmap_str_str)
def parse_ini_section(text: str, section: str) -> PMap[str, str]:
    """Return ``[section]`` from ``text`` as a :class:`PMap` of strings.

    Returns an empty map when the section is missing or ``text`` is empty.
    """
    parser = ConfigParser()
    if not text:
        return pmap()
    parser.read_string(text)
    if not parser.has_section(section):
        return pmap()
    return pmap({key: parser.get(section, key) for key in parser.options(section)})


def _toml_section_pre(text: str) -> bool:
    """Require ``text`` to be a string."""
    return isinstance(text, str)


@beartype
@icontract.require(_toml_section_pre)
@icontract.ensure(_is_pmap_str_object)
def parse_toml_mutmut_section(text: str) -> PMap[str, object]:
    """Parse the ``[tool.mutmut]`` table from ``text`` as a :class:`PMap`."""
    if not text:
        return pmap()
    data = _toml_loads(text)
    if not isinstance(data, Mapping):
        return pmap()
    tool_section = data.get("tool")
    if not isinstance(tool_section, Mapping):
        return pmap()
    raw = tool_section.get("mutmut")
    if not isinstance(raw, Mapping):
        return pmap()
    return pmap(raw)


def _normalize_pre(raw: Mapping[str, object]) -> bool:
    """Require ``raw`` to be a mapping."""
    return isinstance(raw, Mapping)


@beartype
@icontract.require(_normalize_pre)
@icontract.ensure(_is_pmap_str_object)
def normalize_section(raw: Mapping[str, object]) -> PMap[str, object]:
    """Translate legacy ``[tool.mutmut]`` keys to the modern names.

    Deprecated keys (``paths_to_mutate``, ``tests_dir``) are mapped to
    their replacements or dropped, with a :mod:`warnings` note.
    """
    out: PMap[str, object] = pmap()
    for key, value in raw.items():
        if key in ALIAS:
            warnings.warn(
                f"pyproject [tool.mutmut].{key} is deprecated; rename to {ALIAS[key]}",
                UserWarning,
                stacklevel=2,
            )
            out = out.set(ALIAS[key], value)
        elif key in LEGACY_KEYS:
            warnings.warn(
                f"pyproject [tool.mutmut].{key} is deprecated; ignored",
                UserWarning,
                stacklevel=2,
            )
        else:
            out = out.set(key, value)
    return out


def _build_pre(raw: Mapping[str, object], extra_test_files: Sequence[str]) -> bool:
    """Require mapping inputs and a sequence of test files."""
    return isinstance(raw, Mapping) and isinstance(extra_test_files, Sequence)


@beartype
@icontract.require(_build_pre)
@icontract.ensure(_ok_or_mutmut_error)
def build_mutmut_config(
    raw: Mapping[str, object], extra_test_files: Sequence[str]
) -> Result[MutmutConfig, MutmutConfigError]:
    """Build a :class:`MutmutConfig` from the merged raw config map.

    The shell supplies ``extra_test_files`` (from ``Path().glob("test*.py")``)
    so the pure function stays free of filesystem effects.
    """
    source_paths = coerce_str_list(raw.get("source_paths"))
    if not source_paths:
        source_paths = pvector(["scripts"])

    test_selection = coerce_str_list(raw.get("pytest_add_cli_args_test_selection"))
    if not test_selection:
        test_selection = pvector(["tests"])

    also_copy = coerce_str_list(raw.get("also_copy"))
    also_copy = also_copy.append("tests/")
    also_copy = also_copy.append("test/")
    also_copy = also_copy.append("setup.cfg")
    also_copy = also_copy.append("pyproject.toml")
    also_copy = also_copy.extend(str(path) for path in extra_test_files)

    config = MutmutConfig(
        only_mutate=coerce_str_list(raw.get("only_mutate")),
        do_not_mutate=coerce_str_list(raw.get("do_not_mutate")),
        do_not_mutate_patterns=coerce_str_list(raw.get("do_not_mutate_patterns")),
        also_copy=also_copy,
        max_stack_depth=coerce_int(raw.get("max_stack_depth"), -1),
        debug=coerce_bool(raw.get("debug"), False),
        mutate_only_covered_lines=coerce_bool(raw.get("mutate_only_covered_lines"), False),
        source_paths=source_paths,
        pytest_add_cli_args=coerce_str_list(raw.get("pytest_add_cli_args")),
        pytest_add_cli_args_test_selection=test_selection,
        timeout_multiplier=coerce_float(raw.get("timeout_multiplier"), 15.0),
        timeout_constant=coerce_float(raw.get("timeout_constant"), 1.0),
        type_check_command=coerce_str_list(raw.get("type_check_command")),
        use_setproctitle=coerce_bool(raw.get("use_setproctitle"), True),
    )
    return Ok(config)


def _parse_pre(
    pyproject_text: str,
    setup_cfg_text: str,
    extra_test_files: Sequence[str],
) -> bool:
    """Require string inputs and a sequence of test files."""
    return (
        isinstance(pyproject_text, str)
        and isinstance(setup_cfg_text, str)
        and isinstance(extra_test_files, Sequence)
    )


@beartype
@icontract.require(_parse_pre)
@icontract.ensure(_ok_or_mutmut_error)
def parse_mutmut_config(
    pyproject_text: str,
    setup_cfg_text: str,
    extra_test_files: Sequence[str],
) -> Result[MutmutConfig, MutmutConfigError]:
    """Parse pyproject.toml and setup.cfg into a :class:`MutmutConfig`.

    ``pyproject_text`` overrides ``setup_cfg_text`` when both define
    the same key. ``extra_test_files`` is the list of ``test*.py``
    files globbed in the project root by the shell.
    """
    ini_section = parse_ini_section(setup_cfg_text, "mutmut")
    toml_section = parse_toml_mutmut_section(pyproject_text)
    merged: PMap[str, object] = ini_section.update(toml_section)
    normalized = normalize_section(merged)
    return build_mutmut_config(normalized, extra_test_files)


def _filter_pre(argv: Sequence[str]) -> bool:
    """Require ``argv`` to be a sequence of strings."""
    return isinstance(argv, Sequence)


@beartype
@icontract.require(_filter_pre)
@icontract.ensure(_is_pvector_str)
def filter_args(argv: Sequence[str]) -> PVector[str]:
    """Strip shim-controlled flags and unknown long options from ``argv``."""
    out: PVector[str] = pvector()
    skip_next = False
    for token in argv:
        if skip_next:
            skip_next = False
            continue
        if token in STRIP_FLAGS:
            skip_next = True
            continue
        if token.startswith("--") and token not in KNOWN_FLAGS:
            continue
        out = out.append(token)
    return out


__all__ += ["Error", "Ok"]
