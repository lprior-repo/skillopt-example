# Hardening Checklist

## Absolute Laws

- No unsafe, FFI, raw pointers, panic surfaces, unchecked access, unchecked arithmetic, lossy casts, ignored fallible results, hidden I/O, or invented command evidence.

## Inputs And Resources

- External input size cap exists before allocation.
- Parser returns typed errors.
- Boundary parsing creates domain types.
- Loops, retries, queues, recursion, and task spawning have bounds.
- Capacity arithmetic is checked.
- Allocation failure maps to typed errors when graceful recovery is required.

## State And Domain

- Status strings are enums.
- Lifecycle booleans are typestate or explicit transitions.
- Optional lifecycle data lives in the variant that owns it.
- IDs, counters, lengths, timestamps, and units use newtypes when they carry rules.

## Evidence

- Commands claimed in final response actually ran and passed.
- Failing commands are reported with exact blockers.
- Performance claims include workload, command, number, hardware, variance, and profiler/benchmark evidence.
- Required output files exist and JSON parses.
