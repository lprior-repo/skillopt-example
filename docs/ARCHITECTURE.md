## Architecture

Deep dive into the `skillopt-train` package, its module layout, the data
flow during a typical run, the state lifecycle, the `Result` contract, the
provider architecture, the time-function choice, and the public API

## Module Layout

The package lives at `scripts/skillopt_train/`. Each module owns one
concern; cross-module glue is done via the typed `TrainError` hierarchy

```
scripts/skillopt_train/
├── __init__.py           # public API, 67 symbols, lazy provider loader
├── __main__.py           # argparse CLI with subcommands train/ci/leaderboard/diff
├── py.typed              # PEP 561 marker so mypy sees inline annotations
├── errors.py             # TrainError + 8 subclasses, all carrying code+context
├── skill.py              # Skill, REQUIRED_FILES, discover/find/from_path
├── rubric.py             # Rubric dataclass, from_path/from_mapping
├── mutator.py            # Mutator, MutatorMeta, hash_overlay, DEFAULT_PROMPT
├── eval_bridge.py        # run_eval, EvalResult, summary.json parser
├── leaderboard.py        # Leaderboard, LeaderboardEntry, fcntl-locked append
├── budget.py             # Budget, BudgetConfig, BudgetState, PlateauDetector
├── self_critique.py      # CritiqueBlock, build_critique, top_failure_modes
├── diff_report.py        # FailureBucket, FailureDiff, diff_runs, render_markdown
├── train_loop.py         # LoopConfig, LoopState, SkillOptLoop, train_main
├── skill_train.py        # SkillDrivenConfig, SkillDrivenState, SkillDrivenLoop
├── ci_runner.py          # single-step variant for cron/CI
└── providers/
    ├── __init__.py       # exports + lazy __getattr__ for SDK providers
    ├── base.py           # ModelProvider Protocol, ModelRequest/Response, load_provider
    ├── mock.py           # MockProvider, ScriptedTurn, extract_json, make_json_response
    ├── anthropic.py      # AnthropicProvider, anthropic SDK wrapper
    ├── openai.py         # OpenAIProvider, openai SDK wrapper
    └── opencode.py       # OpencodeProvider, shells out to `opencode run`
```

## Data Flow

What happens when you run `skillopt-train run holzman-rust --steps 4`
(the actual CLI shape is `skillopt-train train --config <path>` and the
`run` verb comes from the skill-driven wrapper layer)

```
CLI dispatch
  └── argparse parses subcommand
        │
        ▼
Skill.find(skills_root, "holzman-rust")
  └── Skill.from_path(skills/holzman-rust/)
        ├── checks REQUIRED_FILES
        ├── loads rubric.json -> Rubric
        └── resolves eval.py or eval.sh
        │
        ▼
SkillDrivenConfig.from_skill(skill, data_root="data/holzman-rust")
  └── resolves leaderboard/budget/state paths, reads config.json
        │
        ▼
Budget.load(BudgetConfig.default(), budget_path)   # resume-safe
Leaderboard(leaderboard_path)                      # fcntl-locked
load_provider(config.provider_spec)                # such as "opencode:opencode default"
        │
        ▼
SkillDrivenLoop(config, budget, leaderboard, provider)
  └── Mutator.from_skill(skill, provider, candidate_root, base_overlay)
        │
        ▼
loop.run(max_steps=4)
  └── for _ in range(4):
        │
        ▼
      SkillDrivenLoop.step_once()
        │
        ├── Mutator.propose(step, critique, previous_addendum)
        │     ├── _build_prompt(...)
        │     ├── provider.complete(ModelRequest)        # Opencode/Anthropic/OpenAI/Mock
        │     ├── extract_json(response.text)             # parse addendum + reasoning
        │     ├── _validate_payload(...)                  # non-empty, no forbidden tokens
        │     ├── write SKILL-addendum.md                 # to data/.../candidates/step-NNN/
        │     ├── hash_overlay(...) -> bundle_sha256
        │     └── write mutator.json                      # to candidates/step-NNN/mutator.json
        │
        ├── _eval(candidate_name, overlay) -> EvalResult
        │     └── run_eval(...) -> subprocess.run(eval.py, ...)
        │           └── eval.py writes runs/<run_id>/summary.json
        │           └── parse summary.json for hard/soft/mixed
        │
        ├── state = state.with_step(candidate=...)
        ├── budget.record_step(mixed=..., usd=...)
        ├── _build_critique(eval_result)
        │     ├── diff_runs(baseline_summary, eval_result.summary, rubric)
        │     └── build_critique(diff, k=3) -> CritiqueBlock
        ├── _record(eval_result, meta) -> LeaderboardEntry
        │     └── leaderboard.append(entry)               # fcntl-locked JSONL write
        └── if mixed > best_mixed: state = state.with_best(...)
        │
        ▼
      leaderboard.append writes to leaderboard.jsonl
      budget.save writes to budget.json
      save_state writes loop_state.json
```

## State Lifecycle

Each state file is written at a specific moment in the loop, with
specific atomicity guarantees

| file | written by | when | atomicity |
|---|---|---|---|
| `data/<skill>/leaderboard.jsonl` | `Leaderboard.append` | end of every `step_once` | `fcntl.flock(LOCK_EX)` per line |
| `data/<skill>/budget.json` | `Budget.save` | end of `main` and end of `ci_runner` | write to `*.tmp` then `Path.replace` |
| `data/<skill>/loop_state.json` | `LoopState.save` | end of `main` and end of `ci_runner` | write to `*.tmp` then `Path.replace` |
| `data/<skill>/candidates/step-NNN/SKILL-addendum.md` | `Mutator.propose` | mid-step, after JSON parse | direct write (mutator retries on error) |
| `data/<skill>/candidates/step-NNN/mutator.json` | `Mutator._write_meta` | mid-step, after addendum is written | direct write |
| `data/<skill>/runs/<run_id>/summary.json` | skill's `eval.py` | mid-step, while eval runs | owned by the eval script |

The `loop_state.json` is loaded on `--resume`; the `budget.json` is loaded
on every `Budget.load`; the `leaderboard.jsonl` is append-only and never
rewritten (use `Leaderboard.prune(keep_last=1024)` to compact it)

## How the Result Type Works

The target contract is

```python
Result = Ok[T] | Err[E]
```

Where `Ok[T]` wraps a success value and `Err[E]` wraps a failure value
`E` is constrained to be a `TrainError` subclass so every failure carries
a `code` (string), a `message` (string), and a `context` (dict)

In the current codebase, the `Result` type is not yet a first-class
dataclass; functions that can fail raise typed exceptions instead, the
`errors.py` hierarchy implements the `E` side of the contract today

```python
class TrainError(Exception):
    code: str = "train_error"
    def __init__(self, message, *, code=None, context=None): ...
    def to_dict(self) -> TrainErrorDict: ...

class ConfigError(TrainError):     code = "config_error"
class ProviderError(TrainError):   code = "provider_error"
class BudgetExceeded(TrainError):  code = "budget_exceeded"
class PlateauReached(TrainError):  code = "plateau_reached"
class MutatorError(TrainError):    code = "mutator_error"
class EvalError(TrainError):       code = "eval_error"
class LeaderboardError(TrainError): code = "leaderboard_error"
class DiffError(TrainError):       code = "diff_error"
```

The rule of thumb for callers:

- **Raise** when the failure is structural (bundle missing, eval crashed,
  LLM returned unparseable JSON)
- **Return Result** when the caller is expected to handle both branches
  inline (loader returning a bundle that may be malformed, optional
  feature flag)

The migration to `Result = Ok[T] | Err[E]` is mechanical: replace
`raise TrainError(...)` with `return Err(TrainError(...))` and convert
`try: ... except TrainError as e: ...` sites into `match` on the return
value; the `code` and `context` fields are preserved either way

## Provider Architecture

The `ModelProvider` `Protocol` defines the contract every provider
implements

```python
class ModelProvider(Protocol):
    name: str
    def complete(self, request: ModelRequest) -> ModelResponse: ...
    def health(self) -> Mapping[str, str]: ...
```

Four implementations ship in `scripts/skillopt_train/providers/`

| provider | name | use case | SDK |
|---|---|---|---|
| `MockProvider` | `mock` | unit tests, dry runs, deterministic JSON | none (in-process) |
| `AnthropicProvider` | `anthropic` | Claude Sonnet 4.5, Opus 4.1, Haiku 4.5 | `anthropic` |
| `OpenAIProvider` | `openai` | gpt-4.1, gpt-4o, o3, o4-mini | `openai` |
| `OpencodeProvider` | `opencode` | opencode CLI, swap models freely | `opencode run --pure` |

`load_provider(spec)` parses `name:model` and returns the right instance

```python
spec = "opencode:opencode default"
provider = load_provider(spec)
```

### Lazy `__getattr__` Loader

The three SDK-backed providers (`AnthropicProvider`, `OpenAIProvider`,
`OpencodeProvider`) are NOT imported eagerly from `providers/__init__.py`.
The module defines a `__getattr__` that maps each name to a relative
import path

```python
_LAZY_PROVIDER_MODULES: Final[dict[str, str]] = {
    "AnthropicProvider": ".anthropic",
    "OpenAIProvider": ".openai",
    "OpencodeProvider": ".opencode",
}

def __getattr__(name: str) -> object:
    module_rel = _LAZY_PROVIDER_MODULES.get(name)
    if module_rel is not None:
        module = importlib.import_module(module_rel, __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(...)
```

Why this matters: importing `AnthropicProvider` requires the `anthropic`
package to be installed; if a user only ever runs `--provider mock`, the
`anthropic` and `openai` SDKs are never imported, and a missing optional
dependency does not break `skillopt-train list` or any other mock-only
command; the same trick is applied at the package level in `__init__.py`,
so `from skillopt_train import AnthropicProvider` works but does not pay
the import cost until the attribute is touched

## `time.monotonic()` vs `time.time()`

The codebase uses two different clock APIs and the choice is deliberate

- `time.time()` returns wall-clock seconds since the epoch; it is
  affected by NTP corrections, daylight-savings changes, and manual
  clock adjustments; the loop uses it for `started_at`,
  `BudgetState.started_at`, `LeaderboardEntry.timestamp`, and
  `MutatorMeta.created_at` — anywhere the value is shown to humans
  or compared against an absolute timestamp
- `time.monotonic()` returns a clock that is guaranteed never to go
  backwards; the codebase currently uses `time.time() - started_at`
  to compute elapsed seconds in `Budget` and `SkillOptLoop`; the
  monotonic variant is the intended upgrade path for production
  because a clock jump during a long step would otherwise silently
  extend the apparent elapsed time and could trip the wall-clock
  budget without warning

The practical rule:

- **Display, persistence, cross-process coordination** -> `time.time()`
- **Duration measurement, budget enforcement, retry backoff** -> `time.monotonic()`

## `py.typed` and the Public API

`scripts/skillopt_train/py.typed` is a 9-byte marker file; its presence
tells type checkers (mypy, pyright, pylance) that the package ships inline
type annotations and that downstream code can rely on them

The public surface is enumerated in `__all__` in `__init__.py` and
currently has 67 symbols; the major groupings:

- **Errors (10)**: `TrainError`, `BudgetExceeded`, `ConfigError`,
  `DiffError`, `EvalError`, `LeaderboardError`, `MutatorError`,
  `PlateauReached`, `ProviderError`, plus the alias `Result` and the
  `Ok` / `Err` constructors (declared in `__all__`, lazy-resolved)
- **Skill (3)**: `Skill`, `REQUIRED_FILES`, plus `Skill.from_path` /
  `Skill.find` / `Skill.discover` are class methods
- **Rubric (2)**: `Rubric`, `RubricDict`
- **Mutator (3)**: `Mutator`, `MutatorMeta`, `DEFAULT_PROMPT`
- **Eval (2)**: `EvalResult`, `run_eval`
- **Leaderboard (3)**: `Leaderboard`, `LeaderboardEntry`,
  `best_entry`
- **Budget (4)**: `Budget`, `BudgetConfig`, `BudgetState`,
  `PlateauDetector`
- **Self-critique (2)**: `CritiqueBlock`, plus the helpers
  `build_critique`, `inject_critique`, `top_failure_modes`
- **Diff (4)**: `FailureBucket`, `FailureDiff`, `categorize`,
  `diff_runs`, `render_markdown`
- **Train loops (4)**: `LoopConfig`, `LoopState`, `SkillOptLoop`,
  `SkillDrivenConfig`, `SkillDrivenLoop`
- **Providers (7)**: `ModelProvider`, `ModelRequest`, `ModelResponse`,
  `Usage`, `ScriptedTurn`, `MockProvider`, plus the lazy
  `AnthropicProvider` / `OpenAIProvider` / `OpencodeProvider`
- **Helpers (8)**: `estimate_tokens`, `extract_json`,
  `hash_overlay`, `load_provider`, `make_json_response`, `now_ms`,
  `propose`, `propose_from_skill`
- **CLI entry points (4)**: `ci_main`, `diff_main`, `lb_main`,
  `skill_train_main`, `train_main`

The three SDK-backed providers are exposed via `__all__` but not
imported at module load; `from skillopt_train import AnthropicProvider`
triggers the package-level `__getattr__`, which in turn triggers the
providers-level `__getattr__`, which imports `anthropic` lazily

## When to Use Which Loop

The package ships two loops because they have different configuration
sources

- `SkillOptLoop` reads a JSON `LoopConfig` file; use it when the
  loop parameters are version-controlled but the skill is not a
  self-contained bundle (such as multi-skill campaigns, regression
  suites)
- `SkillDrivenLoop` reads a `Skill` bundle; use it when the skill is
  a first-class artifact that should be discoverable, gradeable, and
  evolvable without an external config

Both share `Budget`, `Leaderboard`, `ModelProvider`, `CritiqueBlock`,
`FailureDiff`, and the same JSON schemas on disk; switching between
them is a one-line change in the calling code

## Threading and Concurrency

The harness is single-process and single-threaded for the loop body
Cross-process safety is provided by `fcntl.flock` on the
`leaderboard.jsonl` file, so multiple `ci_runner` invocations can
append without corrupting the log; `Budget` uses an in-process
`threading.Lock` to guard `record_step` and `check`, allowing a
future multi-thread step body to share a single budget safely
