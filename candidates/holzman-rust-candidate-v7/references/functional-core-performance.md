# Functional Core Performance Reference

Derived from `/home/lewis/.agents/skills/functional-rust/SKILL.md` and its references. This reference is subordinate to Holzman Rust safety and evidence gates.

## Architecture

- Data: inert domain data, zero-copy where lifetime-safe, typed newtypes, enums, typestates, and bounded collections.
- Calculations: pure deterministic functions. No I/O, no clocks, no logging, no network, no persistence, no shared-state mutation.
- Actions: explicit shell for I/O, async, persistence, retries, clocks, logging, metrics, and external APIs.

Move logic from Actions into Calculations, then into Data/types when the domain invariant can be represented by the compiler.

## Type Discipline

- Parse at boundaries into trusted types; do not repeatedly validate primitives inside the core.
- Replace primitive domain APIs with newtypes when the value has domain rules.
- Replace bool lifecycle flags, status strings, and `Option` lifecycle fields with enums or typestates.
- Core errors should be typed domain errors. Shell errors may add context at the boundary.
- Invalid states should be unconstructable or rejected by fallible constructors.

## Performance Defaults

- Prefer borrowed `&str`/`&[u8]`, `Cow`, or caller-owned buffers at parse boundaries when lifetimes make that safe.
- Avoid intermediate `Vec`/`String` allocations in pure pipelines; use lazy iterators or `try_fold` until the final consumer.
- Use caller-owned output buffers or `encode_into` style APIs for hot encoders when that preserves API clarity.
- Use `SmallVec` only when small-size distribution is known and measured.
- Use Rayon only for large pure transforms with scaling evidence; it is not a default for tiny fixed-size data.
- Manual loops are acceptable when they are bounded, clearer for checked errors, avoid allocation, or are measured faster.

## Strict Repair Patterns

- Use `split_once` over collecting split parts when the grammar expects one separator.
- Use `get` or iterator/chunk APIs over unchecked indexing.
- Use `try_reserve` before bounded growth where allocation failure is part of the contract.
- Use `u32::try_from`, `usize::try_from`, or destination-type `try_from` for all length/offset conversions.
- Use checked addition, multiplication, shifts, and division under strict clippy gates.
- Do not report `cargo test`, `cargo fmt`, or `cargo clippy` as passed unless the command was actually run and passed.
