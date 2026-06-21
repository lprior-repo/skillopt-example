# Python-as-Gleam Constitution

Write Python as if it were Gleam. Python is the runtime; Gleam is the discipline. If a construct is illegal in Gleam, it is illegal here. There are no waivers, carve-outs, grandfather clauses, or temporary exceptions.

## Spine

- Use `expression` for `Result`, `Option`, `pipe`, `curry`, `compose`, `Seq`, and `Map`.
- Use `pyrsistent` for `PVector`, `PMap`, and `PSet`.
- Use `icontract` for `@require`, `@ensure`, and invariants.
- Use `crosshair` in CI to prove contracts.
- Use `hypothesis` property tests on public pure functions.
- Do not reimplement these primitives.

## Types

- Every function has full annotations.
- `Any` is banned.
- Bare `dict`, `list`, `set`, and bare `tuple` are banned in every Python file.
- Use `PVector[T]`, `PMap[str, T]`, `PSet[T]`, and `tuple[T, ...]`.
- `Optional[T]` is banned. Use `Option[T]`.
- Two-type unions are sum types. Model them as frozen dataclass variants.
- `# type: ignore` must include a checker code.

## Errors Are Values

- Public functions return `Result[T, E]`, never raise.
- `E` is a frozen dataclass subclass of the project `DomainError`/domain error root.
- `raise` is banned.
- `try/except` is banned.

## Data Is Immutable

- Every dataclass is `@dataclass(frozen=True, slots=True)`.
- Field updates use `dataclasses.replace` or `attrs.evolve`.
- Frozen dataclasses must not contain mutable `list`, `dict`, or `set` fields.
- Mutable local builders are banned.

## Branching

- Use `match`/`case` for variant/type dispatch.
- `if` is allowed for genuine boolean predicates only.
- Matches on sum types must be exhaustive.
- No bare `_` final case on domain variants.

## Composition

- Use `pipe(value, f, g, h)` for multi-step transforms.
- Pipelines use named pure functions, not anonymous lambdas.

## Side Effects

- Every Python module takes values and returns values.
- No Python file is exempt because it is shell code, a test, a benchmark, or vendored code.
- Do not import `subprocess`, `socket`, `httpx`, `requests`, `time`, `random`, or read `os.environ`.
- Do not print or write files from Python code.

## Assurance

- Public functions have `icontract` preconditions and postconditions.
- CrossHair checks every module in CI.
- Every loop has a static bound.
- No `while True`.
- No unbounded recursion.
- No `assert`.
- Hypothesis properties cover every public pure function.
- Mutmut surviving mutants mean the tests are insufficient.

## Banned Constructs

- `eval`, `exec`, `compile`
- `__import__`
- `subprocess.run(..., shell=True)` and equivalent shell escapes
- `os.system`, `os.popen`
- any `except`
- `assert`
- `pickle.loads` on untrusted bytes
- `globals()` or `locals()` for execution
- `print`
- any `raise`
- `# type: ignore` without a code
- mutable default arguments
- `dict[str, Any]` in public signatures
- `try/except`

## Required For New Functions

1. Annotated signature using `expression` and `pyrsistent` types.
2. Returns `Result[T, DomainError]`.
3. Has `icontract` `@require` and `@ensure`.
4. Has at least one Hypothesis property test.
5. Is included in the CrossHair CI path.
6. Has no IO imports or hidden effects.

## Commands

- Use `uv sync --all-groups` to install.
- Use `uv run ...` for every Python tool: `pytest`, `ruff`, `pyright`, `mypy`, `semgrep`, `crosshair`, `mutmut`, `vulture`, and `refurb`.
- Do not invoke `.venv/bin/python`, `python`, `pytest`, `ruff`, or `pyright` directly.

## Review Order

1. Is it pure?
2. Does it return `Result`?
3. Are types complete and free of `Any`?
4. Are collections immutable?
5. Is `match` exhaustive?
6. Are contracts present and CrossHair-proved?
7. Is there a Hypothesis property?
8. Did mutation testing kill the mutants?

If any answer is no, block the change.
