"""Workaround runner for ``mutmut`` 3.6.0 (thin shell).

The shipped ``pyproject.toml`` still uses the deprecated ``tests_dir``
key for ``[tool.mutmut]``. Mutmut 3.6.0 crashes at import time when
that key is present as a string because it tries to concatenate
``[] + "tests"``. Until ``pyproject.toml`` is migrated to
``source_paths`` and ``pytest_add_cli_args_test_selection`` this shim
translates the legacy keys into the new ones before mutmut loads any
module.

All non-trivial logic (INI/TOML parsing, legacy-key normalization,
type coercion, CLI argument filtering) lives in
:mod:`mutmut_runner_core`. This module owns the side effects:
filesystem reads, dynamic imports, monkey-patching ``mutmut``'s
config loader, and process invocation through the CLI shim.
"""

from __future__ import annotations

import importlib as _importlib
import sys
from collections.abc import Sequence
from pathlib import Path

import mutmut.configuration as _cfg

from mutmut_runner_core import (
    MutmutConfig,
    filter_args,
    parse_mutmut_config,
)

_PYPROJECT_PATH = Path("pyproject.toml")
_SETUP_CFG_PATH = Path("setup.cfg")
_TEST_GLOB_PATTERN = "test*.py"


def _read_text(path: Path) -> str:
    """Return ``path`` contents, or the empty string when missing."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _glob_test_files() -> tuple[str, ...]:
    """Glob ``test*.py`` in the project root."""
    return tuple(str(path) for path in Path().glob(_TEST_GLOB_PATTERN))


def _config_from(mutmut: MutmutConfig) -> object:
    """Translate :class:`MutmutConfig` into ``mutmut.configuration.Config``."""
    return _cfg.Config(
        only_mutate=list(mutmut.only_mutate),
        do_not_mutate=list(mutmut.do_not_mutate),
        do_not_mutate_patterns=list(mutmut.do_not_mutate_patterns),
        also_copy=[Path(p) for p in mutmut.also_copy],
        max_stack_depth=mutmut.max_stack_depth,
        debug=mutmut.debug,
        mutate_only_covered_lines=mutmut.mutate_only_covered_lines,
        source_paths=[Path(p) for p in mutmut.source_paths],
        pytest_add_cli_args=list(mutmut.pytest_add_cli_args),
        pytest_add_cli_args_test_selection=list(mutmut.pytest_add_cli_args_test_selection),
        timeout_multiplier=mutmut.timeout_multiplier,
        timeout_constant=mutmut.timeout_constant,
        type_check_command=list(mutmut.type_check_command),
        use_setproctitle=mutmut.use_setproctitle,
    )


def _loader() -> object:
    """Build a ``mutmut.configuration.Config`` from on-disk project files."""
    pyproject_text = _read_text(_PYPROJECT_PATH)
    setup_cfg_text = _read_text(_SETUP_CFG_PATH)
    extra = _glob_test_files()
    result = parse_mutmut_config(pyproject_text, setup_cfg_text, extra)
    match result:
        case object(ok=MutmutConfig() as config):
            return _config_from(config)
        case object(error=err):
            sys.stderr.write(f"[mutmut_config_error] {err}\n")
            sys.exit(1)
    sys.stderr.write("[mutmut_config_error] unexpected result\n")
    sys.exit(1)


def _install_config_loader() -> None:
    """Patch ``mutmut.configuration._load_config`` so it returns our :class:`MutmutConfig`."""
    _cfg._load_config = _loader


def main(argv: Sequence[str]) -> int:
    """Translate argv for mutmut 3.6.0 and dispatch into its CLI."""
    _install_config_loader()
    mutmut_main = _importlib.import_module("mutmut.__main__")
    kept = filter_args(argv)
    mutmut_main.cli(list(kept), standalone_mode=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
