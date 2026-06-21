# Changelog

All notable changes to this project are documented in this file

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [0.2.0] - 2026-06-21

### Added

- Python-as-Gleam constitution (`AGENTS.md`) — 14 sections, 111 lines; type-strict rules: no `Any`, no `Optional[T]`, no mutable dataclasses, errors as `Result[T, E]`, no `raise`, no `try/except`, no `print`, no file writes
- Semgrep rules (`semgrep.yml`) — 18 banned-construct rules enforcing the constitution
- `tests/test_rubric_properties.py` — 67 LOC of hypothesis property tests for the rubric
- `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`, `docs/OUTPUT-FORMAT.md`, `docs/TUTORIAL.md` — project documentation rewritten to match the slimmed-down state
- `LICENSE` (MIT), `SECURITY.md`, `CODE_OF_CONDUCT.md` — standard project meta
- `pyproject.toml` with `package = false` (the project is not published as a package)
- `[tool.pyright]` strict `typeCheckingMode`
- `[tool.mypy]` with `follow_imports = "skip"` and `ignore_missing_imports = true`
- `Taskfile.yml` with 12 tasks: install, lock-upgrade, test, smoke, typecheck, lint, format, fix, ci, clean, build, docs
- `.python-version` pinning Python 3.12
- `semgrep.yml` enforcement of the constitution

### Changed

- Project trimmed to a single supported path: generated corpus + generator + candidate evaluator + SkillOpt adapter + active candidate
- Historical local training loops, bundle examples, old reports, and generated run summaries are intentionally absent
- `pyproject.toml` slimmed to 3 dependencies: openai, pygments, pyyaml
- `Taskfile.yml` reduced from 17 tasks to 12
- `README.md` slimmed from 153 lines to 51 lines
- `CHANGELOG.md` relocated from the repo root to `docs/CHANGELOG.md` (this file)

### Fixed

- The constitution is enforced by semgrep, not just described in `AGENTS.md`

### Removed

- The `scripts/skillopt_train/` package (the AI-native training harness from a previous branch)
- The `skills/` directory (per-skill bundles for the training harness)
- The `data/` directory (was used by the training harness)
- The `bench/` directory (was used for performance benchmarks)
- 5 of 6 example skills (only `candidates/holzman-rust-candidate-v13/` remains)
- The `providers/` directory (LLM adapters for the training harness)
- 6 of 6 subdirectories under `docs/` (only 4 markdown files remain)
- `docs/providers/` (per-provider docs for the removed training surface)

## [0.1.0] - 2026-05-15

### Added

- Initial release: a Holzman Rust SkillOpt workspace with the dataset generator and candidate evaluator
- 13 hand-authored candidate bundles in `candidates/holzman-rust-candidate-v1` through `v13`
- The `vendor/SkillOpt/` SkillOpt trainer package
- Documentation site in `docs/skillopt-site/`
