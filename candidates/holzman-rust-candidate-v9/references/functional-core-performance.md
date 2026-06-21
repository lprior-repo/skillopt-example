# Functional Core Performance Reference

This reference is subordinate to the absolute laws in `SKILL.md`.

## Architecture

- Data is inert, valid by construction, and carries domain meaning through newtypes, enums, typestates, and bounded collections.
- Calculations are pure deterministic functions with no I/O, clocks, logging, randomness, metrics, shared mutation, persistence, network, or environment access.
- Actions are the shell: I/O, async, persistence, retries, clocks, logging, metrics, environment access, and external APIs.
- Move logic from actions into calculations, then into data/types when the invariant can be represented by the compiler.

## Repair Patterns

- Use `split_once` over collecting split parts when the grammar expects one separator.
- Use `get`, `chunks_exact`, iterators, or proven bounds over unchecked indexing.
- Use `try_reserve` after validating capacity against a trusted cap.
- Use destination-type `try_from` for every width conversion.
- Use checked addition, multiplication, shifts, and division under strict clippy gates.
- Do not discard `#[must_use]` results.

## Performance Defaults

- Prefer borrowed data and caller-owned buffers when ownership is not required.
- Avoid intermediate `Vec`/`String` allocations unless materialization is required.
- Use `ArrayVec`/`SmallVec` only when size distribution and benchmark justify them.
- Use Rayon only for large independent work with scaling evidence.
- Manual bounded loops are acceptable when they make error handling and allocation behavior clearer.
