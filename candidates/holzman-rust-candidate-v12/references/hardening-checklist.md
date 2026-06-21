# Hardening Checklist

- No unsafe, FFI, raw pointers, panic surfaces, unchecked access, unchecked arithmetic, lossy casts, ignored fallible results, hidden I/O, or invented command evidence.
- External input size cap exists before allocation.
- Parser returns typed errors.
- Boundary parsing creates domain types.
- Loops, retries, queues, recursion, and task spawning have bounds.
- Capacity arithmetic is checked.
- Allocation failure maps to typed errors when graceful recovery is required.
- Status strings are enums.
- Lifecycle booleans are typestate or explicit transitions.
- Optional lifecycle data lives in the variant that owns it.
- IDs, counters, lengths, timestamps, and units use newtypes when they carry rules.
- Commands claimed in final response actually ran and passed.
- Required output files exist and JSON parses.
