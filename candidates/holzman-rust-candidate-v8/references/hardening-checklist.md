# Hardening Checklist

Use this checklist for real-repo work, promotion review, or high-risk repairs.

## Inputs And Boundaries

- External input size cap exists before allocation.
- Parser returns typed errors, not panics or strings.
- Boundary parsing creates domain types.
- Core logic does not revalidate raw primitives repeatedly.

## Resource Bounds

- Loops, retries, queue growth, worker spawning, recursion, and traversal have static or domain caps.
- Capacity arithmetic is checked.
- Allocation failure is mapped to typed errors when graceful recovery is required.
- Hot paths have an allocation budget when performance matters.

## State And Domain

- Status strings are enums.
- Lifecycle booleans are typestate or explicit transitions.
- Optional lifecycle data lives in the variant that owns it.
- IDs, counters, lengths, timestamps, and units use newtypes when they carry rules.

## Low-Level Safety

- Unsafe is absent or covered by an explicit waiver.
- FFI wrappers document and test ownership, nullability, length, alignment, lifetime, aliasing, initialization, and unwind behavior.
- SIMD has scalar fallback, target-feature gate, remainder handling, and tests.

## Evidence

- Commands claimed in the final response actually ran and passed.
- Failing commands are reported with exact blockers.
- Performance claims include workload, command, number, hardware, variance, and profiler/benchmark evidence.
- Required output files exist and JSON parses.
