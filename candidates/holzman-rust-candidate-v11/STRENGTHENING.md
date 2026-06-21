# Candidate v11 Strengthening Notes

Candidate v11 tightens v10 around observed full-run failures.

## Changes From v10

- Frame/packet encoder recipe now says checked capacity arithmetic and `try_reserve` are mandatory even when behavior tests pass without them.
- Typestate review now requires a separate `parse_boundary` finding whose text literally contains both `parse` and `boundary`.
- Review output now says every finding must include a numeric `line`, using nearest source line if exact line is uncertain.

## Status

- Candidate-only.
- Requires full validation/test on exact v11 bundle before any promotion decision.
