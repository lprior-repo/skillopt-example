# Security Policy

## Supported Versions

The latest released version receives security updates
Older versions are not patched

## Reporting a Vulnerability

Report security issues via GitHub Security Advisories at the project repository; do not file public issues for vulnerabilities

When reporting, include:
- Description of the vulnerability
- Reproduction steps
- Potential impact
- Suggested fix (if any)

Response targets:
- Initial acknowledgment: within 7 days
- Triage and fix timeline: within 30 days for high-severity issues

## Out of Scope

The following are not considered security vulnerabilities:
- Hallucinated model outputs (the harness drives LLMs; outputs are not security boundaries)
- Cost overruns from intentional full evaluation runs; use provider-side quotas and the evaluator's explicit promotion gate
- Candidate bundles under `candidates/`; treat them as developer-supplied content and run them only in sandboxed environments
