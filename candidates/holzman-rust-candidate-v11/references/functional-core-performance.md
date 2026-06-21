# Functional Core Performance Reference

Subordinate to the absolute laws in `SKILL.md`.

- Data is inert and valid by construction through newtypes, enums, typestates, and bounded collections.
- Calculations are pure deterministic functions with no I/O, clocks, logging, randomness, metrics, shared mutation, persistence, network, or environment access.
- Actions are shell work: I/O, async, persistence, retries, clocks, logging, metrics, environment access, and external APIs.
- Parse at boundaries into trusted values.
- Use `split_once` for one-separator grammars.
- Use `get`, `chunks_exact`, iterators, or proven bounds over unchecked indexing.
- Use `try_reserve` after validating capacity against a trusted cap.
- Use destination-type `try_from` for every width conversion.
- Use checked addition, multiplication, shifts, and division under strict clippy gates.
- Do not discard `#[must_use]` results.
- Avoid intermediate `Vec`/`String` allocations unless materialization is required.
- Use Rayon, SmallVec, SIMD, zero-copy, arenas, or custom allocation only with workload and benchmark evidence.
