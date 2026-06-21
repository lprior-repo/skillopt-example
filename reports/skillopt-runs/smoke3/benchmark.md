# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-19T22:21:34.890715+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `accept_new_best`
- Current score: 0.363
- Best score: 0.363
- Best step: 1

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 2 | 0.000 | 0.663 | 0.331 | 0 |
| candidate-v1 | 2 | 0.000 | 0.725 | 0.363 | 0 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | review_unbounded_parser | review | 0.0 | 0.375 | missing_groups=[['external input', 'untrusted input', 'boundary']]; mutation_errors=added:Cargo.lock,added:target/.rustc_info.json,added:target/CACHEDIR.TAG,added:target/debug/.cargo-build-lock,added:target/debug/.cargo-lock,added:target/debug/.fingerprint/review_unbounded_parser-1d65dba4dc395e52/dep-lib-review_unbounded_parser,added:target/debug/.fingerprint/review_unbounded_parser-1d65dba4dc395e52/invoked.timestamp,added:target/debug/.fingerprint/review_unbounded_parser-1d65dba4dc395e52/lib-review_unbounded_parser,added:target/debug/.fingerprint/review_unbounded_parser-1d65dba4dc395e52/lib-review_unbounded_parser.json,added:target/debug/.fingerprint/review_unbounded_parser-f7e588900e84b211/dep-test-lib-review_unbounded_parser,added:target/debug/.fingerprint/review_unbounded_parser-f7e588900e84b211/invoked.timestamp,added:target/debug/.fingerprint/review_unbounded_parser-f7e588900e84b211/test-lib-review_unbounded_parser,added:target/debug/.fingerprint/review_unbounded_parser-f7e588900e84b211/test-lib-review_unbounded_parser.json,added:target/debug/deps/libreview_unbounded_parser-1d65dba4dc395e52.rmeta,added:target/debug/deps/libreview_unbounded_parser-f7e588900e84b211.rmeta,added:target/debug/deps/review_unbounded_parser-1d65dba4dc395e52.d,added:target/debug/deps/review_unbounded_parser-f7e588900e84b211.d,added:target/debug/incremental/review_unbounded_parser-0bb46b2xyoys5/s-hjmt11ike0-0rvwu08-3lnxev9p3g3zhr0gmfbkrh4c9/dep-graph.bin,added:target/debug/incremental/review_unbounded_parser-0bb46b2xyoys5/s-hjmt11ike0-0rvwu08-3lnxev9p3g3zhr0gmfbkrh4c9/query-cache.bin,added:target/debug/incremental/review_unbounded_parser-0bb46b2xyoys5/s-hjmt11ike0-0rvwu08-3lnxev9p3g3zhr0gmfbkrh4c9/work-products.bin,added:target/debug/incremental/review_unbounded_parser-0bb46b2xyoys5/s-hjmt11ike0-0rvwu08.lock,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt11ik2k-1iv1ict-byty6mu83mka2rgig6alaergb/dep-graph.bin,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt11ik2k-1iv1ict-byty6mu83mka2rgig6alaergb/metadata.rmeta,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt11ik2k-1iv1ict-byty6mu83mka2rgig6alaergb/query-cache.bin,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt11ik2k-1iv1ict-byty6mu83mka2rgig6alaergb/work-products.bin,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt11ik2k-1iv1ict.lock,added:target/flycheck0/stderr,added:target/flycheck0/stdout |
| baseline | repair_byte_at | repair | 0.0 | 0.950 | json_invalid |
| candidate-v1 | review_unbounded_parser | review | 0.0 | 0.500 | mutation_errors=added:Cargo.lock,added:target/.rustc_info.json,added:target/CACHEDIR.TAG,added:target/debug/.cargo-build-lock,added:target/debug/.cargo-lock,added:target/debug/.fingerprint/review_unbounded_parser-1d65dba4dc395e52/dep-lib-review_unbounded_parser,added:target/debug/.fingerprint/review_unbounded_parser-1d65dba4dc395e52/invoked.timestamp,added:target/debug/.fingerprint/review_unbounded_parser-1d65dba4dc395e52/lib-review_unbounded_parser,added:target/debug/.fingerprint/review_unbounded_parser-1d65dba4dc395e52/lib-review_unbounded_parser.json,added:target/debug/.fingerprint/review_unbounded_parser-f7e588900e84b211/dep-test-lib-review_unbounded_parser,added:target/debug/.fingerprint/review_unbounded_parser-f7e588900e84b211/invoked.timestamp,added:target/debug/.fingerprint/review_unbounded_parser-f7e588900e84b211/test-lib-review_unbounded_parser,added:target/debug/.fingerprint/review_unbounded_parser-f7e588900e84b211/test-lib-review_unbounded_parser.json,added:target/debug/deps/libreview_unbounded_parser-1d65dba4dc395e52.rmeta,added:target/debug/deps/libreview_unbounded_parser-f7e588900e84b211.rmeta,added:target/debug/deps/review_unbounded_parser-1d65dba4dc395e52.d,added:target/debug/deps/review_unbounded_parser-f7e588900e84b211.d,added:target/debug/incremental/review_unbounded_parser-0bb46b2xyoys5/s-hjmt2cfc55-12p8zex-91ldx6993orxam6hs7f1v74je/dep-graph.bin,added:target/debug/incremental/review_unbounded_parser-0bb46b2xyoys5/s-hjmt2cfc55-12p8zex-91ldx6993orxam6hs7f1v74je/query-cache.bin,added:target/debug/incremental/review_unbounded_parser-0bb46b2xyoys5/s-hjmt2cfc55-12p8zex-91ldx6993orxam6hs7f1v74je/work-products.bin,added:target/debug/incremental/review_unbounded_parser-0bb46b2xyoys5/s-hjmt2cfc55-12p8zex.lock,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt2cfc4z-0q0ygv2-1axoqnsfk6sk5icjp782gtrrc/dep-graph.bin,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt2cfc4z-0q0ygv2-1axoqnsfk6sk5icjp782gtrrc/metadata.rmeta,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt2cfc4z-0q0ygv2-1axoqnsfk6sk5icjp782gtrrc/query-cache.bin,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt2cfc4z-0q0ygv2-1axoqnsfk6sk5icjp782gtrrc/work-products.bin,added:target/debug/incremental/review_unbounded_parser-24yf2ntbc318h/s-hjmt2cfc4z-0q0ygv2.lock,added:target/flycheck0/stderr,added:target/flycheck0/stdout |
| candidate-v1 | repair_byte_at | repair | 0.0 | 0.950 | json_invalid |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/smoke3/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/smoke3/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/smoke3/tasks`
