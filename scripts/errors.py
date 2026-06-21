"""Canonical error ADT for the skill-moo project.

The project models every failure as a frozen dataclass value rather than
an exception. This module is the single source of truth for those error
values; public pure functions return ``Result[T, DomainError]`` and the
variants defined here are the only legitimate ``E`` types.

Two domain hierarchies are defined:

* :class:`DatasetError` for failures during dataset assembly.
* :class:`EvalError` for failures during candidate skill evaluation.

Use the per-variant factory helpers (e.g. :func:`manifest_missing`,
:func:`unknown_split`) to construct values without restating the
machine-readable ``code`` field, which the variants supply by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ruff: noqa: N818
# Variant class names inherit the ``*Error`` suffix of their parent
# hierarchies, so N818 (``exception class name should end in Error``)
# would otherwise demand ``ManifestMissingError`` and similar. The
# canonical names from the spec intentionally omit the suffix.


@dataclass(frozen=True, slots=True)
class DomainError:
    """Root of the project error hierarchy.

    Every typed error value inherits from this class. Subclasses are
    frozen, slotted dataclasses so that error values are immutable,
    hashable, and cheap to compare in tests. The ``__str__`` form is
    ``"[{code}] {message}"`` to preserve the shell layer's
    ``RunError(message, code=code)`` log semantics.
    """

    code: str
    message: str

    def __str__(self) -> str:
        """Render the error as ``[code] message`` for log output."""
        return f"[{self.code}] {self.message}"


@dataclass(frozen=True, slots=True)
class DatasetError(DomainError):
    """Errors raised when assembling or validating the dataset."""


@dataclass(frozen=True, slots=True)
class EvalError(DomainError):
    """Errors raised when evaluating a candidate skill bundle."""


# --- DatasetError variants ---


@dataclass(frozen=True, slots=True, kw_only=True)
class ManifestMissing(DatasetError):
    """The required manifest file was not found on disk."""

    manifest_path: str
    code: str = field(default="manifest_missing")


def manifest_missing(manifest_path: str) -> ManifestMissing:
    """Build a :class:`ManifestMissing` error for ``manifest_path``."""
    return ManifestMissing(
        message=f"manifest missing: {manifest_path}",
        manifest_path=manifest_path,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class InvalidSplit(DatasetError):
    """The dataset does not contain the requested split name."""

    split: str
    code: str = field(default="invalid_split")


def invalid_split(split: str) -> InvalidSplit:
    """Build an :class:`InvalidSplit` error for ``split``."""
    return InvalidSplit(
        message=f"invalid split: {split}",
        split=split,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class InvalidDoctrine(DatasetError):
    """The dataset doctrine identifier is not recognised."""

    doctrine: str
    code: str = field(default="invalid_doctrine")


def invalid_doctrine(doctrine: str) -> InvalidDoctrine:
    """Build an :class:`InvalidDoctrine` error for ``doctrine``."""
    return InvalidDoctrine(
        message=f"invalid doctrine: {doctrine}",
        doctrine=doctrine,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class TaskAssemblyFailure(DatasetError):
    """A task family could not be assembled from the dataset."""

    family: str
    code: str = field(default="task_assembly_failure")


def task_assembly_failure(family: str) -> TaskAssemblyFailure:
    """Build a :class:`TaskAssemblyFailure` error for ``family``."""
    return TaskAssemblyFailure(
        message=f"task assembly failure: {family}",
        family=family,
    )


# --- EvalError variants ---


@dataclass(frozen=True, slots=True, kw_only=True)
class UnknownSplit(EvalError):
    """The eval pipeline received a split name that the adapter does not expose."""

    split: str
    code: str = field(default="unknown_split")


def unknown_split(split: str) -> UnknownSplit:
    """Build an :class:`UnknownSplit` error for ``split``."""
    return UnknownSplit(
        message=f"unknown split: {split}",
        split=split,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class MissingSkillMd(EvalError):
    """The candidate directory does not contain a SKILL.md file."""

    skill_path: str
    code: str = field(default="missing_skill_md")


def missing_skill_md(skill_path: str) -> MissingSkillMd:
    """Build a :class:`MissingSkillMd` error for ``skill_path``."""
    return MissingSkillMd(
        message=f"missing SKILL.md: {skill_path}",
        skill_path=skill_path,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class UnsupportedConfig(EvalError):
    """The eval config is well-formed but unsupported by the harness."""

    reasons: tuple[str, ...]
    code: str = field(default="unsupported_config")


def unsupported_config(reasons: tuple[str, ...]) -> UnsupportedConfig:
    """Build an :class:`UnsupportedConfig` error listing the given ``reasons``."""
    return UnsupportedConfig(
        message="unsupported config: " + ", ".join(reasons),
        reasons=reasons,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class EmptySelection(EvalError):
    """The selected items for a split are empty after filtering."""

    split: str
    code: str = field(default="empty_selection")


def empty_selection(split: str) -> EmptySelection:
    """Build an :class:`EmptySelection` error for ``split``."""
    return EmptySelection(
        message=f"no items selected for split={split}",
        split=split,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateMissing(EvalError):
    """The candidate bundle is absent from disk."""

    path: str
    code: str = field(default="candidate_missing")


def candidate_missing(path: str) -> CandidateMissing:
    """Build a :class:`CandidateMissing` error for ``path``."""
    return CandidateMissing(
        message=f"candidate missing: {path}",
        path=path,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigInvalid(EvalError):
    """The eval config file is malformed or fails validation."""

    path: str
    code: str = field(default="config_invalid")


def config_invalid(path: str) -> ConfigInvalid:
    """Build a :class:`ConfigInvalid` error for ``path``."""
    return ConfigInvalid(
        message=f"config invalid: {path}",
        path=path,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class EvalManifestMissing(EvalError):
    """The candidate's eval manifest is absent from disk."""

    manifest_path: str
    code: str = field(default="manifest_missing")


def eval_manifest_missing(manifest_path: str) -> EvalManifestMissing:
    """Build an :class:`EvalManifestMissing` error for ``manifest_path``."""
    return EvalManifestMissing(
        message=f"manifest missing: {manifest_path}",
        manifest_path=manifest_path,
    )


__all__ = [
    "CandidateMissing",
    "ConfigInvalid",
    "DatasetError",
    "DomainError",
    "EmptySelection",
    "EvalError",
    "EvalManifestMissing",
    "InvalidDoctrine",
    "InvalidSplit",
    "ManifestMissing",
    "MissingSkillMd",
    "TaskAssemblyFailure",
    "UnknownSplit",
    "UnsupportedConfig",
    "candidate_missing",
    "config_invalid",
    "empty_selection",
    "eval_manifest_missing",
    "invalid_doctrine",
    "invalid_split",
    "manifest_missing",
    "missing_skill_md",
    "task_assembly_failure",
    "unknown_split",
    "unsupported_config",
]
