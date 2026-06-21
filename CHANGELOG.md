# Changelog

All notable changes to `skill-moo` are documented in this file

The format follows Keep a Changelog and the project adheres to Semantic Versioning

## [0.2.0] - 2026-06-21

### Added
- The `Skill` type with discovery and lookup: `Skill.from_path`, `Skill.find`, `Skill.discover`, `Skill.load_prompt`, `Skill.load_default_config`
- The `Rubric` type with declarative configuration: `Rubric.from_path`, `Rubric.from_mapping`, `Rubric.to_mapping`, `Rubric.bucket_for_token`
- The `Mutator.from_skill` factory that loads the prompt template and forbidden tokens from a `Skill` instance
- The `propose_from_skill` convenience function
- The `SkillDrivenLoop` class that drives propose→grade→keep_best for a `Skill` without manual `LoopConfig` wiring
- The `SkillDrivenConfig` class that derives paths from a `Skill` instance
- The `skillopt-train run <skill_name>` CLI subcommand
- The `skillopt-train list` CLI subcommand
- The `skills/holzman-rust/` example skill bundle with `SKILL.md`, `rubric.json`, `prompt.md`, `tasks.jsonl`, `eval.py`, `config.json`, `references/`
- The `skills/react-typescript/` example skill bundle with the same structure
- 14 unit tests for `Skill` and `Rubric` in `tests/test_skill.py`
- 9 unit tests for `SkillDrivenLoop` in `tests/test_skill_train.py`
- 3 unit tests for the CLI in `tests/test_cli.py`
- 7 discovery tests in `tests/test_skill_discovery.py`
- Property tests for `Skill` and `Rubric` in `tests/test_skill_properties.py`
- End-to-end integration tests in `tests/test_integration.py`

### Changed
- `diff_report.categorize` and `diff_report.diff_runs` now take an optional `Rubric` argument; the hardcoded `_FORBIDDEN_TOKEN_MAP` and `_GRADE_RETURNCODE_KEYS` are now loaded from the rubric
- `train_loop.SkillOptLoop` passes `Rubric.default()` to `diff_runs` for backward compatibility
- The CLI now has 6 subcommands: `train`, `ci`, `leaderboard`, `diff`, `run`, `list`
- `__init__.py` re-exports `Skill`, `SkillDrivenConfig`, `SkillDrivenLoop`, `Rubric`, `RubricDict`, `REQUIRED_FILES`, `skill_train_main`, `propose_from_skill`
- The `Skill` discovery convention is `skills/<name>/` with required files: `SKILL.md`, `rubric.json`, `prompt.md`, `tasks.jsonl`, plus `eval.py` or `eval.sh`

### Fixed
- The harness is now truly skill-agnostic: any skill that follows the bundle convention can be evolved without changing the `skillopt_train` source code
- Domain knowledge (forbidden tokens, grade keys, prompts) moved from Python source to per-skill `rubric.json` and `prompt.md` files
- The leaderboard now carries the skill name in `entry.extras["skill"]`

### Removed
- The hardcoded `_FORBIDDEN_TOKEN_MAP` in `diff_report.py` is no longer the source of truth — it lives in `skills/<name>/rubric.json` now
- The `DEFAULT_PROMPT` constant in `mutator.py` is no longer the only prompt — `skills/<name>/prompt.md` is the new source of truth

## [0.1.0] - 2026-06-01

### Added
- Initial release of the `skill-moo` SkillOpt harness for the Holzman Rust doctrine
- `SkillOptLoop` with `propose`, `grade`, `keep_best`, and `LoopConfig`/`LoopState` types
- `Budget` and `PlateauDetector` for resource-aware search
- `MockProvider` plus pluggable `AnthropicProvider`, `OpenAIProvider`, `OpencodeProvider`
- `Leaderboard` with `best_entry` selection and JSONL persistence
- `diff_report` module with `categorize`, `diff_runs`, and `render_markdown`
- CLI entry point `skillopt-train` with `train`, `ci`, `leaderboard`, and `diff` subcommands
- Holzman Rust dataset generation and candidate evaluation scripts under `scripts/`
- Vendor copy of `SkillOpt` core under `vendor/SkillOpt/`