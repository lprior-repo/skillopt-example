# Candidate-v2 Review Report

**Date:** 2026-06-19
**Reviewer:** Qwen 5090
**Files reviewed:**
- `candidates/holzman-rust-candidate-v2/SKILL-addendum.md`
- `candidates/holzman-rust-candidate-v2/references/review-output-contract.md`
- `scripts/holzman_skillopt_eval.py`
- `reports/skillopt-runs/full1/benchmark.md`
- `reports/holzman-skillopt-optimization.md`

---

## 1. Does candidate-v2 fix candidate-v1's repair timeout risk?

**Verdict: Partial mitigation. Structural risk remains.**

Candidate-v1's catastrophic failure was not a logic bug — it timed out on all 6 repair tasks (opencode_returncode=124). The agent consumed its full wall-clock budget without producing valid `repair-output.json`.

Candidate-v2's addendum addresses this in two ways:

1. **Narrowed repair scope** (lines 24-38): The repair fast path is an explicit checklist: read skill + references, read Cargo.toml/source/tests, make smallest production change, run `cargo test`/fmt/clippy. This is a genuine improvement over v1, which had no structured repair procedure.
2. **Gate-skipping language** (line 38): Explicitly forbids running `cargo audit`, `cargo deny`, `cargo vet`, `cargo geiger`, `cargo machete`, `cargo hack`, `cargo mutants`, benchmarks, docs, and other supply-chain gates "unless explicitly requested." This directly addresses the hypothesis that the agent was stalling on self-directed gate execution.

**However, three structural risks remain:**

- **The timeout is at the opencode execution layer, not the skill layer.** The harness default timeout is 300s (`scripts/holzman_skillopt_eval.py:744`). Even with a tightly scoped addendum, the LLM may still take too long to produce the JSON output. The addendum constrains *what* the agent does, but not *how fast* it reasons.
- **Repair prompt still requires `cargo test` + `cargo clippy` + `cargo fmt --check`.** These are synchronous, potentially slow operations. If the model stalls before issuing them, the skill guidance is moot.
- **No timeout-aware behavior.** The addendum does not tell the agent: "if you cannot complete within a reasonable time, produce partial output." There is no degradation strategy — it's all-or-nothing.

**Recommendation:** Add a repair-degradation clause to the addendum: if the agent cannot complete all gates, produce the best-effort JSON output with `skipped_gates` populated. This converts a hard timeout failure into a graded penalty.

---

## 2. Is the harness candidate versioning/cache safe?

**Verdict: Safe for single-run isolation. No cross-run contamination.**

The harness materializes bundles via `materialize_bundles()` (`scripts/holzman_skillopt_eval.py:109-151`):

- Copies source skill to `baseline/` and `candidate-v2/` directories under `run_root/bundles/`.
- Appends the addendum to `candidate/SKILL.md`.
- Copies reference files from the overlay into `candidate/references/`.
- Computes `digest_tree()` hashes for both bundles and records them in a manifest.

Sandbox workdirs live under `/tmp/opencode/holzman-skillopt/<run-id>/` and are wiped at the start of each run (`scripts/holzman_skillopt_eval.py:752-754`).

**Safety properties:**
- No shared state between runs (different `run_id` = different sandbox).
- No cross-candidate leakage (baseline and candidate are independent copies).
- Digests enable post-hoc verification that a bundle was not modified between materialization and execution.

**Limitations:**
- No per-candidate caching across runs. Every run recreates bundles from scratch. This is fine for correctness but means runs are expensive (each needs full skill materialization).
- `resume` mode (`--resume` flag, line 743) reuses `grade.json` but does NOT verify the bundle digests match. If the candidate overlay changes and you resume, you'd grade stale bundle results against new bundle structure. This is a minor risk — the flag is intended for retrying failed tasks, not for reusing results across candidate iterations.

**Recommendation:** Add a digest check in the resume path: if `grade.json` exists but the bundle digest changed, invalidate the cached grade.

---

## 3. Is this still a comparator rather than true SkillOpt training?

**Verdict: This is a single-shot comparator. No iterative training loop exists.**

The harness runs baseline and candidate on the same 12 tasks, computes aggregate hard/soft/mixed scores, and passes them to `evaluate_gate()` (`scripts/holzman_skillopt_eval.py:778-790`). The gate returns an action (`accept`/`reject`) based on whether candidate beats baseline on the mixed metric.

**Why this is a comparator, not training:**

1. **`global_step=1`, `best_step=0`** (line 787-788). There is only one comparison step. True SkillOpt would iterate: modify skill, re-evaluate, compare, accept or reject the modification.
2. **No feedback-to-edit loop.** The candidate overlay is manually authored (`SKILL-addendum.md`), not produced by the harness. The harness does not generate or apply modifications.
3. **Single comparison.** The gate compares two fixed bundles. There is no mechanism for the harness to produce candidate-v3 based on v2's failures.
4. **`best_skill="baseline"` is hardcoded** (line 785). The gate's "current" and "best" are both set to baseline, meaning the gate can only ever accept candidate-v2 or reject it. There is no concept of "best candidate" evolving.

This is a valid and useful pattern — it's a **candidate comparator** that decides whether a manually-authored skill modification is an improvement. It is not a SkillOpt training loop. The report at `reports/holzman-skillopt-optimization.md` correctly calls it a "comparator" in its description (line 5 of `benchmark.md`).

**Recommendation:** If the goal is true SkillOpt-style iteration, the harness would need:
1. A skill-modification step that takes the candidate's failures and produces an updated addendum.
2. A loop that re-runs the comparator with the updated candidate.
3. Convergence criteria (max iterations, score plateau detection).

Until then, this is a well-designed comparator with a clear acceptance/rejection gate.

---

## Summary

| Question | Answer |
|---|---|
| Does v2 fix v1's repair timeout risk? | Partially. Narrowed scope and gate-skipping help, but no degradation strategy exists for when the agent still times out. |
| Is candidate versioning/cache safe? | Yes for single runs. Resume mode has a minor digest-mismatch risk. |
| Is this SkillOpt training? | No. Single-shot comparator only. No iterative loop, no auto-modification, no convergence. |

**Overall assessment:** Candidate-v2 is a reasonable, minimal improvement over v1. The repair fast path is well-structured and directly addresses the scope-creep hypothesis. However, without a timeout-degradation strategy and with the structural limitation of being a one-shot comparator, the evaluation framework remains incomplete for automated skill evolution.
