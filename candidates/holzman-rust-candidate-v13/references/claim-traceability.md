# Claim Traceability

Holzman Rust controls. Functional Rust is subordinate and supplies architecture only where it strengthens Holzman.

| Claim | Source | Candidate Rule |
|---|---|---|
| Simple bounded control flow | Holzman Power of Ten | Every loop, iterator, retry, traversal, stream, and worker drain needs a static/domain bound or proof. |
| No post-init allocation in critical paths | Holzman Power of Ten | Critical paths allocate during initialization only; hot paths need allocation budgets and evidence. |
| Panic freedom | Holzman + Functional | No unwrap/expect/panic/assert paths in production; typed errors instead. |
| Checked results and inputs | Holzman + Functional | Never ignore fallible results; parse at boundaries. |
| Data/Calculations/Actions | Functional under Holzman | Pure core plus action shell, with Holzman bounds and evidence. |
| Invalid states unrepresentable | Holzman + Functional | Newtypes, enums, typestates, smart constructors. |
| No hidden side effects | Functional under Holzman | I/O/logging/metrics/persistence stay in shell. |
| Performance claims | Holzman PLUS | Workload, hardware, baseline, new number, variance, threshold, profiler/benchmark evidence. |
| Functional performance tools | Functional under Holzman | Cow/Bytes/SmallVec/Rayon/zero-copy require measured workload and resource evidence. |
| Static dispatch | Holzman PLUS | Hot paths prefer generics/enums/direct calls; dynamic dispatch requires measured need. |
| Dense runtime IR | Holzman Runtime Architecture | Repeated runtime evaluation of accepted human/spec/config data compiles to prevalidated compact IR. |
| Evidence gates | Holzman | Canonical repo gate first; fallback strict source gate; classify failures. |

Conflict resolutions:

- Bounded explicit loops beat forced iterator pipelines when they are clearer, simpler, or easier to prove.
- Local `mut` is allowed when narrow and justified by clarity, bounded buffers, or measured hot-path performance.
- ArrayVec is for hard bounds; SmallVec is for measured small-common-case with acceptable fallback allocation.
- Rayon is only for large independent pure transforms with scaling evidence.
- Zero-copy is preferred when lifetimes stay simple; owned data is allowed when it is simpler, safer, or required by the shell boundary.
