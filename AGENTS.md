# Python Constitution

You write Python as if it were Gleam with Rust's assurance. Python is the
runtime; Gleam is the discipline; Rust is the bar.

## Non-negotiables

1. Pure core, thin shell. Side effects only in `io/` and `*_shell.py`.
2. Errors are values: `Result[T, DomainError]`, never `raise` outside shell.
3. Data is immutable: `frozen=True, slots=True` on every dataclass; collections
   are `PVector`/`PMap`/`PSet`.
4. Branching is `match` with exhaustive variants and `assert_never` fallback.
5. Trust boundaries parse with `msgspec.json.decode(Schema, raw, strict=True)`.
6. Every public pure function has `@beartype`, `@icontract.require`,
   `@icontract.ensure`, a `@given` hypothesis test.
7. Composition uses `pipe(...)`, not nested calls; name every step.
8. Optional is banned — use `Option[T]` from `expression`.
9. No `Any`, no bare `dict`/`list`, no `cast(...)` outside shell.
10. `uv run` is the only entry point. `uv.lock` is committed and frozen in CI.

## When you write a function

- Annotate every parameter and return type, fully.
- Return `Result[T, E]` if it can fail. `E` is a typed dataclass subclass of
  the domain error.
- Add `@beartype` and `icontract` `@require` / `@ensure`.
- Use `match` for any non-trivial branch. Sum types are frozen dataclass
  variants.
- Use `pipe` for multi-step transforms.
- If you need to parse, the function belongs in `io/`. Pure functions take
  already-typed values.

## When you write a test

- Property test first (`@given`). Example test only for regression pinning.
- Stateful domains get a `hypothesis.stateful.RuleBasedStateMachine`.
- Mutation testing must kill every mutant on changed lines.
- Coverage gate is 90% on changed lines (`diff-cover`).

## When you review code

In order, reject if:
1. Any mutation outside the shell.
2. Any `raise` outside the shell.
3. Any `Any`, bare `dict`/`list`, `Optional`, `T | None` return.
4. Any non-exhaustive `match`.
5. Missing `icontract` contracts on a public pure function.
6. Missing `@given` property test on a public pure function.
7. Any `json.loads`, `yaml.safe_load`, `eval`, `shell=True`.
8. Any `# type: ignore` without a code.
9. Any `lambda` inside `pipe(...)`.
10. Any `@dataclass` without `frozen=True, slots=True`.

"We can clean it up later" is how this constitution dies. Block the PR.

## Environment

    uv sync
    uv run pyright
    uv run pytest

That's the loop. If `uv run` doesn't have it, it doesn't exist.

## CI gates (all mandatory)

    uv sync --frozen
    uv run ruff format --check
    uv run ruff check
    uv run semgrep --config semgrep.yml
    uv run pyright
    uv run crosshair check scripts/
    uv run pytest
    uv run mutmut run
    uv run diff-cover coverage.xml --fail-under=90
    uv run interrogate --fail-under=100 scripts/
    uv run deptry scripts/
    uv tool run pip-audit --strict

No gate is optional. No gate is a warning.