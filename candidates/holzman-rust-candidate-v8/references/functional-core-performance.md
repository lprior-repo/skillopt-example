# Functional Core Performance Reference

This reference is subordinate to Holzman safety, bounded-resource, and evidence gates.

## Architecture

- Data is inert, valid by construction, and carries domain meaning through newtypes, enums, typestates, and bounded collections.
- Calculations are pure deterministic functions with no I/O, clocks, logging, randomness, metrics, shared mutation, persistence, network, or environment access.
- Actions are the shell: I/O, async, persistence, retries, clocks, logging, metrics, environment access, and external APIs.
- Move logic from actions into calculations, then into data/types when the invariant can be represented by the compiler.

## Type Discipline

- Parse at boundaries into trusted values.
- Replace primitive domain APIs with value objects when the value has domain rules.
- Replace bool lifecycle flags, status strings, and lifecycle `Option` fields with enums or typestates.
- Core errors should be typed domain errors.
- Shell errors may add context at the boundary.

## Performance Defaults

- Prefer borrowed `&str`/`&[u8]`, caller-owned buffers, or `Cow` when ownership is not required.
- Avoid intermediate `Vec`/`String` allocations in pure pipelines unless a materialized collection is required.
- Use caller-owned output buffers or `encode_into` style APIs for hot encoders when that preserves clarity.
- Use `ArrayVec`/`SmallVec` only when the size distribution and benchmark justify them.
- Use Rayon only for large independent work with scaling evidence.
- Manual loops are acceptable when they are bounded, clearer for checked errors, avoid allocation, or benchmark faster.

## Strict Repair Patterns

- Use `split_once` over collecting split parts when the grammar expects one separator.
- Use `get`, `chunks_exact`, or proven bounds over unchecked indexing.
- Use `try_reserve` only after validating the target capacity against a trusted cap.
- Use destination-type `try_from` for all width conversions.
- Use checked addition, multiplication, shifts, and division under strict clippy gates.
- Do not report command success unless the command actually ran and passed.
