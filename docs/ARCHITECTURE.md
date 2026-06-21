## Architecture

Deep dive into the Holzman Rust SkillOpt workspace — module layout, data flow, promotion rules, the Python-as-Gleam constitution enforced by semgrep, and the CI gate

The supported path is exactly two scripts and one test, plus a vendored SkillOpt trainer; everything else is either docs, generated corpus, candidate bundle, or third-party vendor

## Module Layout

ASCII tree of the actual project:

```
skill-moo/                                # Holzman Rust SkillOpt workspace
├── AGENTS.md                             # Python-as-Gleam constitution
├── README.md                             # Quickstart + supported path
├── pyproject.toml                        # UV-managed, no pip
├── Taskfile.yml                          # 12 tasks: install/test/lint/typecheck/ci
├── semgrep.yml                           # 19 banned-construct rules
├── LICENSE / SECURITY.md / CODE_OF_CONDUCT.md
├── docs/
│   ├── ARCHITECTURE.md                   # this file
│   ├── GLOSSARY.md                       # domain terms
│   ├── OUTPUT-FORMAT.md                  # file schemas
│   └── TUTORIAL.md                       # worked examples
├── scripts/
│   ├── generate_holzman_rust_dataset.py   # 1454 LOC, deterministic dataset generator
│   └── run_holzman_candidate_eval.py      # 477 LOC, candidate evaluator
├── tests/
│   └── test_rubric_properties.py         # 67 LOC, hypothesis property tests
├── candidates/
│   └── holzman-rust-candidate-v13/       # active candidate bundle
│       ├── SKILL.md                      # the skill body
│       └── references/                   # supporting reference docs
├── data/
│   └── holzman_rust_aggressive/          # generated corpus (regenerated, not committed)
│       ├── manifest.json                 # seed + splits + family map
│       ├── train/items.json              # 227 fixtures
│       ├── val/items.json                # 80 fixtures
│       └── test/items.json               # 80 fixtures
└── vendor/
    └── SkillOpt/                         # third-party SkillOpt trainer
        └── skillopt/envs/holzman_rust/   # the env adapter
            └── rollout.py                # the grader/rollout entry point
```

### Notes on the layout

- Two empty legacy directories (`scripts/skillopt_train/` and `scripts/skillopt_train/providers/`) survive as stale `__pycache__/` only; the active source lives at the top level of `scripts/`
- The `vendor/SkillOpt/` tree contains the full SkillOpt trainer plus its plugins, configs, ckpt, datasets, scripts, tests, and webui; only `skillopt/envs/holzman_rust/` is in the typecheck and lint paths under this project
- `data/holzman_rust_aggressive/` is the generated corpus, regenerated via `task test` and committed only by intent; the manifest pins seed `42` and counts `train=227 val=80 test=80`
- `candidates/holzman-rust-candidate-v13/SKILL.md` plus `references/` is the only active bundle; rollout picks the `SKILL.md` body, hashes it, and feeds it to the adapter

## Data Flow

ASCII flow showing the supported path:

```
generate_holzman_rust_dataset.py
  --seed 42
  --out data/holzman_rust_aggressive
  -> 387 deterministic task fixtures
  -> 227 train + 80 val + 80 test
  -> split by family_id, no leakage

run_holzman_candidate_eval.py
  --candidate-dir candidates/holzman-rust-candidate-v13
  --tasks data/holzman_rust_aggressive
  --splits val,test
  --out <run-dir>
  -> invokes vendor/SkillOpt/skillopt/envs/holzman_rust/rollout.py
  -> rollout runs the model on each task
  -> grader scores each task against the rubric
  -> aggregates hard/soft scores per split
  -> writes <run-dir>/summary.json
  -> exit 0 if both splits hit hard 1.0 (promotable)
  -> exit 1 if a split missed the threshold
  -> exit 2 if the run is non-promotable by config or flags
```

### Generator in detail

- `generate_holzman_rust_dataset.py` enumerates 20 domain families (`case00`..`case19`) across 9 task families
- Review task families: `review_hidden_io`, `review_invalid_state`, `review_black_hat`, `review_functional`, `review_perf_folklore`, `review_unsafe`
- Repair task families: `repair_csv`, `repair_summary`, `repair_frame`, `repair_holzman_header`, `repair_functional_registration`
- Each `TaskDict` carries `id`, `kind`, `family_id`, `domain_family_id`, `split_family_id`, `task_type`, `description`, `files`, `doctrines`, `expected_output_groups`, `expected_source_groups`, `forbidden_source_patterns`, and `forbidden_output_patterns`
- `split_by_family` packs 387 tasks into train/val/test at ratios `0.60/0.20/0.20` with `_SPLIT_RATIOS`, picks `val`/`test`/`train` greedily by `projected_assignment_error`, and pins one black-hat family per split to guarantee coverage
- The manifest records seed, totals, split counts, sorted family list, and `split_families` mapping; the evaluator reads this manifest and validates its sha256

### Evaluator in detail

- `run_holzman_candidate_eval.py` is the only entry point; it validates the candidate bundle (must contain `SKILL.md`), flattens the SkillOpt config, asserts the config uses `split_mode=split_dir` pointing at `data/holzman_rust_aggressive`, asserts `limit=0` and empty `data_path`/`split_output_dir`, then invokes the rollout adapter for each requested split
- Promotion eligibility is computed before any rollout: `splits == ["val","test"]`, no `--ids`, `kind == "all"`; otherwise the run is flagged `non_promotable` with reason and exits `2`
- Per-split summaries land at `<run-dir>/full_<split>/summary.json`; the rollup `summary.json`, `bundle_hashes.json`, and `run_metadata.json` sit at `<run-dir>/`
- Hard score averages per row; soft score averages per row; per-split `hard >= 1.0` and `soft >= 0.0` are reported; `fail_reasons` map task id to grader reason
- Exit codes: `0` both splits at hard `1.0` and promotable; `1` a split missed the threshold; `2` non-promotable by config or flags

## Promotion Rules

The README pins these six rules for a run to be `promotable`:

- Full `val,test` (no `--splits train`)
- `--kind all`
- No `--ids` (no targeting)
- `limit: 0` (no limit)
- The checked-in generated split directory (`data/holzman_rust_aggressive` matching empty `data_path` and `split_dir` equal to the canonical path)
- Hard `1.0` on both splits

If any of these is violated, the run is `non_promotable` and the script exits `2`

### Config-side checks (`_config_errors`)

- `split_mode` must equal `split_dir`
- `split_dir` must resolve to `data/holzman_rust_aggressive`
- `data_path` must be empty
- `split_output_dir` must be empty
- `limit` must equal `0`
- `data/holzman_rust_aggressive/manifest.json` must exist

Any config error raises `RunError(code="unsupported_config")` and the script exits `1`

### Promotion-side checks (`_promotion_status`)

- `splits == ["val","test"]` else reason `splits_must_be_val_test`
- `ids` empty else reason `targeted_ids_selected`
- `kind == "all"` else reason `kind=<value>`

The script returns `0` only when both splits hit hard `1.0`; otherwise `1` (some split missed the threshold) or `2` (not promotable)

### Bundle hashing

- `bundle_hashes` walks the candidate dir, hashes `SKILL.md`, and recursively hashes every file under `references/`
- The hashes are written to `<run-dir>/bundle_hashes.json` and embedded in `<run-dir>/run_metadata.json` so a run is reproducible from the same hash triple: candidate + config + corpus manifest

## Constraints from AGENTS.md

The Python-as-Gleam constitution — the rules from `AGENTS.md` in force today:

### Spine

Use `expression` for `Result`, `Option`, `pipe`, `curry`, `compose`, `Seq`, and `Map`; use `pyrsistent` for `PVector`, `PMap`, `PSet`; use `icontract` for `@require`, `@ensure`, invariants; use `crosshair` in CI; use `hypothesis` property tests on public pure functions; do not reimplement these primitives

### Types

Every function has full annotations; `Any` is banned; bare `dict`, `list`, `set`, and bare `tuple` are banned in every Python file; use `PVector[T]`, `PMap[str, T]`, `PSet[T]`, and `tuple[T, ...]`; `Optional[T]` is banned, use `Option[T]`; two-type unions are sum types modeled as frozen dataclass variants; `# type: ignore` must include a checker code

### Errors Are Values

Public functions return `Result[T, E]`, never raise; `E` is a frozen dataclass subclass of the project `DomainError`/domain error root; `raise` is banned; `try/except` is banned

### Data Is Immutable

Every dataclass is `@dataclass(frozen=True, slots=True)`; field updates use `dataclasses.replace` or `attrs.evolve`; frozen dataclasses must not contain mutable `list`, `dict`, or `set` fields; mutable local builders are banned

### Branching

Use `match`/`case` for variant/type dispatch; `if` is allowed for genuine boolean predicates only; matches on sum types must be exhaustive; no bare `_` final case on domain variants

### Composition

Use `pipe(value, f, g, h)` for multi-step transforms; pipelines use named pure functions, not anonymous lambdas

### Side Effects

Every Python module takes values and returns values; no Python file is exempt because it is shell code, a test, a benchmark, or vendored code; do not import `subprocess`, `socket`, `httpx`, `requests`, `time`, `random`, or read `os.environ`; do not print or write files from Python code

### Assurance

Public functions have `icontract` preconditions and postconditions; CrossHair checks every module in CI; every loop has a static bound; no `while True`; no unbounded recursion; no `assert`; Hypothesis properties cover every public pure function; Mutmut surviving mutants mean the tests are insufficient

### Required For New Functions

Every new function needs all six: annotated signature using `expression` and `pyrsistent` types; returns `Result[T, DomainError]`; has `icontract` `@require` and `@ensure`; has at least one Hypothesis property test; is included in the CrossHair CI path; has no IO imports or hidden effects

### Commands

Install with `uv sync --all-groups`; run every Python tool through `uv run` — `pytest`, `ruff`, `pyright`, `mypy`, `semgrep`, `crosshair`, `mutmut`, `vulture`, `refurb`; never invoke `.venv/bin/python`, `python`, `pytest`, `ruff`, or `pyright` directly

## Banned Constructs (from semgrep.yml)

The 19 semgrep rules the constitution enforces:

1. `python.no-dynamic-execution` — no `eval`/`exec`/`compile`
2. `python.no-dunder-import` — no `__import__`
3. `python.no-shell-escape` — no `os.system`/`os.popen`/`subprocess.run(..., shell=True)`
4. `python.no-type-ignore-without-code` — type ignores must name a checker code
5. `python.no-any` — no `Any` annotation
6. `python.no-optional` — no `Optional[T]`, use `expression.Option[T]`
7. `python.no-mutable-collection-annotations` — no bare `list[T]`/`dict[K,V]`/`set[T]`
8. `python.no-mutable-dataclass` — must be `frozen=True, slots=True`
9. `python.no-assert` — no `assert`
10. `python.no-print` — no `print`
11. `python.no-raise` — no `raise`
12. `python.no-except` — no `try/except`/`try/finally`
13. `python.no-subprocess` — no `subprocess` import
14. `python.no-network-imports` — no `socket`/`httpx`/`requests`
15. `python.no-env-time-random` — no `os.environ`/`time.X`/`random.X`
16. `python.no-file-writes` — no `Path.write_text`/`Path.write_bytes`/`Path.mkdir`/`open(..., "w"|"a"|"x"|"+")`
17. `python.no-mutable-defaults` — no `def f(x=[])`/`x={}`/`x=set()`
18. `python.no-unsafe-pickle-loads` — no `pickle.loads`
19. `python.no-execution-introspection` — no `globals()`/`locals()` (for execution)

## CI Gate

The repo has no `.github/workflows/*.yml`; the local `task ci` is the gate, and it runs the following steps in order:

1. `task install` — `uv sync --dev`
2. `task lint` — `ruff check` over the three first-party Python files plus `vendor/SkillOpt/skillopt/envs/holzman_rust/rollout.py`
3. `task typecheck` — `mypy` over the same three files with `strict=false`, `ignore_missing_imports=true`, `follow_imports=skip`
4. `task test` — `python -m py_compile` over the same three files, then regenerate the corpus into `/tmp/holzman_rust_aggressive_check` with `--seed 42`
5. `task smoke` — print `run_holzman_candidate_eval.py --help` to confirm the evaluator still parses

### Other Taskfile targets

- `lock-upgrade` — `uv lock --upgrade` followed by `uv sync --dev`
- `format` — `ruff format` over the three first-party files plus the rollout adapter
- `fix` — `ruff check --fix` over the same set
- `clean` — remove `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `dist`, `build`, `.venv`, and `__pycache__` trees
- `build` — `uv build` wheel and sdist (the project is `package=false` so this is mostly a smoke)
- `docs` — `head -20 README.md`

### Pyproject pin

The `pyright.include`, `mypy.files`, and `ruff.src` lists all pin the same three first-party files plus the rollout adapter; `vendor/`, `data/`, `docs/`, `reports/`, `runs/`, `candidates/`, and `dist/` are excluded everywhere except where the env adapter is consulted

The `[tool.uv] package = false` setting marks the project as non-distributable; the wheel build in `task build` is a smoke test, not a release path