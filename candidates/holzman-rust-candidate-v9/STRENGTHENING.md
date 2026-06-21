# Candidate v9 Strengthening Notes

Candidate v9 corrects v8 by restoring the strict laws as absolute, non-waivable constraints.

## Changes From v8

- Removed waiver policy for unsafe, FFI, raw pointers, unchecked access/arithmetic, lossy casts, and panic surfaces.
- Declared existing impossible violations as blockers rather than waiver candidates.
- Removed FFI implementation guidance because this doctrine does not use FFI.
- Moved high-frequency repair obligations near the top so agents see them before broader architecture guidance.
- Reintroduced explicit `try_reserve`, `checked_add`, `checked_div`, `try_from`, `split_once`, typestate, parse-boundary, bounded-allocation, and fixed-array review obligations needed by prior failures.
- Kept v8's useful mode distinction, output validation, resource caps, semantic review contract, and real-repo gate.

## Status

- Candidate-only.
- Requires full validation/test on exact v9 bundle before any promotion decision.
