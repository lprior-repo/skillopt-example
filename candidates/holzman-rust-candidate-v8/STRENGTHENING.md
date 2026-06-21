# Candidate v8 Strengthening Notes

Candidate v8 is a text hardening pass over v7. It has not replaced any live skill.

## What Changed From v7

- Added portable skill frontmatter.
- Added operating modes for review, repair, implementation, performance, eval/sandbox, and real-repo work.
- Added first-pass triage protocol for scope, side effects, hostile input, and blockers.
- Replaced blanket eval assumptions with separate eval/sandbox and real-repo test policies.
- Added waiver policy for unsafe, FFI, raw pointers, unchecked access, public API breaks, broad test rewrites, and speed-first nightly features.
- Hardened bounded allocation guidance to require absolute caps before `try_reserve`.
- Added semantic review requirements to reduce keyword-laundry findings.
- Added required output read-back and JSON validation discipline.
- Added real-repo fallback verification gate based on strict source linting and command truth.
- Added async/concurrency, FFI, resource-bound, and promotion-boundary sections.
- Kept v7's useful anti-regression repair patterns, but framed them as context-dependent patterns rather than universal recipes.

## Why It Is Stronger

- It is less overfit to the synthetic CSV/frame/summary dataset.
- It is safer for live repositories because tests, APIs, unsafe, allocation, and verification now have explicit mode-dependent rules.
- It reduces DoS risk from naive `try_reserve(max_items)` instructions.
- It makes missing JSON output and invented command claims first-class failures.
- It gives reviewers a semantic contract rather than a checklist of magic words.

## Current Status

- Not evaluated with the SkillOpt harness yet.
- Not promotion-safe until full validation/test are rerun on the exact v8 bundle and compared against the current live skill.
