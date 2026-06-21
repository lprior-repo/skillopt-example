# Candidate-v5 Final Review — qwen5090

**Date:** 2026-06-20
**Author:** Automated review
**Scope:** SKILL-addendum.md, review-output-contract.md, eval script, three benchmark runs

---

## 1. What Candidate-v5 Changes

The addendum is 66 lines — intentionally small. It adds four constructs to the existing Holzman Rust skill:

1. **Scope boundary enforcement** — hard rule to refuse parent/sibling/eval/candidate/report inspection unless explicitly named. Blocks cross-task leakage.
2. **Review mode grading contract** — findings must be independently gradable: exact rule name, file/line, concrete failure mode, BLOCKER/MAJOR/MINOR severity, smallest fix direction, missing evidence as findings.
3. **Repair fast path** — read-only-first (skill + refs + Cargo.toml + src + tests before editing), smallest production change, typed errors, bounded allocation, `cargo fmt` + `cargo test` gates, explicit gate-skip list for throwaway evals.
4. **Required eval repair patterns** — `try_reserve` + max_items guard for comma/line Vec parsing, `checked_div` + `try_from` for averages, ban on raw `/` and `as` in production repair output.

The review-output-contract reference defines the JSON shape the review tasks produce. Candidate-v5's scope boundary says to read it when present — a clean addition.

## 2. Review of Candidate-v5 Design Quality

### 2.1 Strengths

- **Scope boundary is the single most important addition.** It directly prevents a failure mode seen in LLM evals: agent inspects sibling tasks, reads task manifests, or discovers repo structure beyond the task crate. This is not over-specified — it's the minimal safe boundary.
- **Repair fast path is tight.** The read-before-edit rule, smallest-change principle, and explicit gate-skip list (no `cargo audit`, `cargo deny`, `cargo vet`, etc. for throwaway evals) keep repair tasks fast and predictable. The existing skill had implicit repair behavior; v5 makes it explicit.
- **Required patterns are practical.** `try_reserve` + max_items and `checked_div` + `try_from` are the exact shapes needed for the CSV parser and checked-average repair tasks. The ban on raw `/` and `as` is a strict clippy alignment.
- **Review output contract is well-shaped.** Semantic findings (not just banned-word lists) with failure_mode and fix fields make the grading function's `match_groups` checks meaningful.
- **66 lines is disciplined.** The addendum does not add new gates, new tools, or new evaluation criteria. It constrains and clarifies existing behavior. This is low-risk modification.

### 2.2 Weaknesses / Concerns

- **Scope boundary could be too aggressive.** "Do not inspect parent directories, sibling eval tasks, repo-level evals, candidates, reports, or manifests unless the prompt explicitly names them" is correct for safety but could prevent legitimate cross-reference checks if a task references a sibling crate within a workspace. The skill does not distinguish between "malicious eval leakage" and "legitimate workspace dependencies." However, this is a low-severity concern because the eval tasks are designed as isolated crates.
- **Required patterns are eval-specific, not general.** The `try_reserve`/`checked_div` patterns are written for the repair eval tasks specifically. If deployed on real Rust code, the skill would produce overly prescriptive patterns. This is fine for a comparator eval but worth noting if v5 is intended for broader use.
- **No explicit mention of the existing skill's Power-of-Ten verification gates.** The addendum says "without weakening any existing... verification gate" but does not reference them. If a repair task requires a Verus proof, the fast path's "smallest production-source change" rule might conflict with proof-writing obligations. Again, the eval tasks don't test this, but it's an architectural gap.

## 3. Promotion Risk Assessment

### 3.1 Review Evals (qwen5090-review-v5)

| Metric | Baseline | Candidate-v5 | Delta |
|---|---|---|---|
| Hard | 1.000 | 1.000 | 0.000 |
| Soft | 1.000 | 1.000 | 0.000 |
| Mixed | 1.000 | 1.000 | 0.000 |
| Passed | 6/6 | 6/6 | 0 |

**Gate action: `reject`** — candidate did not beat baseline because baseline was already at the ceiling.

**Risk: LOW but uninformative.** The review eval is saturated. Both bundles achieve perfect scores on all 6 review tasks. This tells us candidate-v5 does not degrade review quality — but it also proves nothing. The grading function's `match_groups` checks, `json_valid` validation, and mutation/execution error penalties are all passing because the tasks are relatively simple static reviews. The eval is not discriminative for review work.

### 3.2 Repair Evals (qwen3090-repair-v5)

| Metric | Baseline | Candidate-v5 | Delta |
|---|---|---|---|
| Hard | 0.167 | 0.333 | +0.166 |
| Soft | 0.850 | 0.886 | +0.036 |
| Mixed | 0.508 | 0.610 | +0.102 |
| Passed | 1/6 | 2/6 | +1 |

**Gate action: `accept_new_best`** — candidate beats baseline on mixed score.

**Risk: MODERATE.** This is the only run where candidate-v5 shows a meaningful improvement. The +0.166 hard delta is driven by `repair_checked_average` (baseline 0.0, candidate 1.0) and `repair_remove_unsafe_copy` (baseline 0.0, candidate 0.0 but soft 0.950 vs 0.700). The baseline fails on 5 of 6 tasks; the candidate fails on 4 of 6. Both are struggling — this is a hard eval suite.

Key observations:
- **`repair_frame_encoder` and `repair_bounded_retries` still fail for candidate-v5** with `missing_groups=['try_reserve']` and `missing_groups=['try_reserve', 'reserve']`. The addendum explicitly teaches `try_reserve` + max_items, yet the model still misses it on these tasks. This suggests the pattern is recognized but not reliably applied — or the grading `match_groups` function (which checks for substring presence in combined output) is not matching because the model uses `reserve` without `try_` prefix in some outputs.
- **`repair_csv_u16` and `repair_remove_unsafe_copy` pass soft scoring but fail hard.** The baseline has no hard passes on these; candidate-v5 gets soft scores of 0.900 and 0.950 respectively but not full hard because the `missing_groups` checks don't fully match. This is a grading sensitivity issue: the eval expects specific tokens (`try_reserve`, `try_from`, etc.) and the model may produce them with slight variations.

### 3.3 Smoke Repair (qwen3090-repair-smoke-v5)

| Metric | Baseline | Candidate-v5 | Delta |
|---|---|---|---|
| Hard | 0.000 | 1.000 | +1.000 |
| Soft | 0.883 | 1.000 | +0.117 |
| Mixed | 0.442 | 1.000 | +0.558 |
| Passed | 0/2 | 2/2 | +2 |

**Gate action: `accept_new_best`** — candidate dominates.

**Risk: HIGH — overfitting signal.** This is the strongest result, but also the most suspect. Only 2 tasks (both also in the full repair suite), and both are tasks where the baseline had the specific failure modes that the addendum targets: `repair_csv_u16` (try_reserve pattern) and `repair_checked_average` (try_from pattern). The addendum was literally written to fix these exact tasks. A 1.0 vs 0.0 hard gap on these two tasks is expected and does not prove general improvement.

## 4. Split GPU Eval Assessment

The evals are split across two model runs:
- **qwen5090-review-v5:** 6 review tasks on qwen5090
- **qwen3090-repair-v5:** 6 repair tasks on qwen3090
- **qwen3090-repair-smoke-v5:** 2 repair tasks on qwen3090 (subset)

### 4.1 Validity

The split is **structurally valid** for comparator evaluation:
- Each bundle (baseline vs candidate-v5) runs on the same tasks in the same run.
- The SkillOpt gate compares bundle scores within each run, not across runs.
- The model difference (5090 vs 3090) does not affect the comparator because both bundles are evaluated identically within each run.

### 4.2 Limitations

- **Review and repair are on different models.** This means we cannot determine if candidate-v5's repair advantage holds on qwen5090, or if its review parity holds on qwen3090. There is no cross-model, cross-task comparison. If the repair advantage is model-specific (e.g., qwen3090 benefits more from the explicit patterns), the eval does not capture it.
- **Smoke eval is a subset of the full repair eval.** The smoke tasks (csv_u16, checked_average) are the same tasks where candidate-v5 shows the strongest delta. This is by design (quick validation) but means the smoke result is not independent of the full repair result.

### 4.3 Recommendation on Split

The split is **acceptable for a first-pass comparator check** but insufficient for promotion. A full eval should run both bundles on both model types across all 12 tasks (6 review + 6 repair) to eliminate model-specific artifacts.

## 5. Overfitting Risk Assessment

### 5.1 Evidence of Overfitting

1. **Smoke eval tasks overlap with full eval tasks.** The 2 smoke tasks (csv_u16, checked_average) are in the 6-task repair suite. Candidate-v5's 1.0 vs 0.0 smoke advantage is entirely explained by these 2 tasks, which the addendum was specifically designed to address. No independent task set validates the generalization.

2. **Review eval saturation.** Both bundles score 1.0 on all review tasks. If candidate-v5 is overfit to repair patterns, the review tasks should still be unaffected (they test different behaviors). The perfect score is consistent with no degradation but also provides no signal.

3. **Repair eval partial success.** Candidate-v5 passes `repair_checked_average` (hard 1.0) — exactly the task the `checked_div` + `try_from` pattern targets. But it still fails `repair_frame_encoder` and `repair_bounded_retries` on `try_reserve`. The pattern is not uniformly applied. This suggests the model recognizes the patterns but does not internalize them as general principles.

### 5.2 Overfitting Risk Level

**MODERATE.** The candidate-v5 changes are narrowly targeted at the repair eval tasks and produce measurable improvement on those specific tasks. However:
- The review eval shows no degradation (good sign).
- The repair improvement is real but partial (not universal across repair tasks).
- The smoke eval's perfect score is not independent evidence.

The risk is that candidate-v5 is overfit to the specific eval task distribution. If deployed on unseen Rust crates, the model might:
- Over-apply `try_reserve` where it's not needed.
- Miss non-pattern repair tasks (e.g., unsafe code cleanup, async boundary fixes).
- Be overly constrained by the scope boundary on workspace projects.

## 6. Comparator-Not-Training Verification

The eval script (`holzman_skillopt_eval.py`) implements a comparator eval:
- Materializes baseline and candidate bundles from the same source skill.
- Runs identical tasks against both bundles.
- Compares aggregate scores via SkillOpt's `evaluate_gate`.
- The candidate overlay only appends to SKILL.md; it does not modify the baseline.
- No training, fine-tuning, or model parameter updates occur.

**This remains comparator-not-training.** The SkillOpt gate only decides accept/reject based on aggregate scores. It does not produce gradient updates or model modifications. The eval is a pure A/B comparison.

## 7. Overall Assessment

| Dimension | Rating | Notes |
|---|---|---|
| Design quality | GOOD | Small, focused, low-risk additions |
| Review eval signal | LOW | Saturated at 1.0 for both bundles |
| Repair eval signal | MODERATE | +0.102 mixed delta, real but partial improvement |
| Overfitting risk | MODERATE | Smoke tasks overlap with full eval; repair patterns are task-specific |
| Split eval validity | ACCEPTABLE | Within-run comparator is valid; cross-model gap is a limitation |
| Comparator-not-training | CONFIRMED | Pure A/B eval, no model modifications |
| Promotion readiness | NOT READY | Repair improvement is promising but not fully validated |

### 7.1 Recommended Actions

1. **Run a full cross-model eval.** Run both bundles on both qwen5090 and qwen3090 across all 12 tasks. This eliminates the split-model artifact and provides independent signals.
2. **Add independent repair tasks.** Create 2-3 new repair tasks that do not overlap with the existing 6. Test scenarios not targeted by the addendum's explicit patterns (e.g., unsafe code cleanup, async boundary fixes, error handling refactoring).
3. **Investigate `try_reserve` failures.** `repair_frame_encoder` and `repair_bounded_retries` still fail on `try_reserve` for candidate-v5 despite the addendum teaching it. This could be a grading sensitivity issue (token matching), a model issue, or a task complexity issue. Examine the raw task artifacts (`repair-output.json`, changed files) to determine the root cause.
4. **Decide on scope boundary relaxation.** If the skill is intended for workspace projects, the scope boundary should distinguish between "eval leakage" and "legitimate workspace cross-references."

### 7.2 Final Verdict

Candidate-v5 is **NOT READY for promotion** at this time. The repair improvement is promising (+0.102 mixed, +1 hard pass), and there is no evidence of review degradation. However, the overfitting risk is moderate, the split eval does not provide full cross-validation, and two repair tasks still fail despite explicit pattern instruction. A full cross-model eval with independent repair tasks should precede any promotion decision.

If the goal is incremental improvement with low risk, candidate-v5 is a reasonable candidate for a limited promotion (repair-only) pending the cross-model validation. The changes are small, targeted, and do not degrade existing behavior.
