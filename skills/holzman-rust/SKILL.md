# Holzman-Rust Skill Bundle

NASA/JPL Power-of-Ten inspired Rust rules for safe, reviewable code.

## Hard Rules

- Never use `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, or `unreachable!` in production code
- Never use `unsafe` blocks or functions marked `unsafe`
- Never use `dbg!` macro in production paths
- Never use `assert!`; rely on types and explicit error handling instead
- Never use `as` for lossy conversions (`as_conversions` is a clippy warning)
- Never index or slice without bounds checking
- Never rely on integer arithmetic side effects
- Never slice strings by byte range
- Never `.get(...).unwrap()` or `.get_mut(...).unwrap()`
- Never panic inside functions that return `Result<T, E>`
- Never use `let _ = expr` to silence `must_use` warnings

## Required Error Handling

Every fallible path must propagate a typed error using `Result<T, E>` where `E` is a meaningful error type defined for the module. Helper modules return errors, never `panic`. The `?` operator is the canonical way to bubble failures up.

## Required Coverage Gates

Every change must pass:

- `cargo fmt --all -- --check`
- `cargo clippy --all-targets --all-features -- -D warnings`
- `cargo test --all-features`
- `cargo audit` for known security advisories
- `cargo deny check` for license and advisory policy
- `cargo vet` for supply-chain provenance
- `cargo geiger` for unsafe surface area
- `cargo machete` for unused dependencies
- `cargo mutants` for mutation coverage
- `cargo +nightly udeps` is recommended

## Documentation Rules

Every public function, struct, enum, trait, and module carries a doc comment. Examples in doc comments must compile. The `missing_docs` lint is deny-by-default.

## Module Layout

- One type per file when the type exceeds 80 lines
- Group related small types in one module under a `mod.rs`
- `lib.rs` is a flat index, not a god module

## No Periods

This skill bundle is prose, but every prose sentence in source code, error messages, and CLI descriptions ends without a period; the period rule is enforced by the Holzman skill itself.