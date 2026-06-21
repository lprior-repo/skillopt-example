# Stress Test Plan

Use this to pressure future candidates beyond the current synthetic fixtures.

## Required Lanes

- Full `data/holzman_rust_aggressive` validation and test splits.
- Repeat full test on the exact candidate hash to measure stochastic missing-output failures.
- Baseline comparison against the current live Holzman skill.
- Near-miss Functional Rust prompts where Rayon, SmallVec, zero-copy, no-loops, or no-mut would be wrong without measurement.
- Real-repo smoke repairs that require source/test bifurcation and canonical gate handling.

## Adversarial Cases To Add

- Bounded explicit loop is clearer than iterator chain.
- `SmallVec` bloats a hot struct and loses to `Vec` or array.
- Rayon is slower for tiny data.
- Zero-copy lifetime complexity is worse than a bounded owned copy.
- Domain primitive is acceptable in a DTO but illegal in core.
- Production assert must become typed error.
- Missing output JSON despite correct reasoning.
- `unwrap_or_default` hides a domain error.
- Static dispatch wins over `dyn Trait` in a hot loop.
- Dense IR is warranted for repeated policy/config evaluation.
