# Security Policy

## Scope

holodeck-serial is a research simulation framework with no network-facing
components, authentication systems, or sensitive data handling. The attack
surface is minimal by design.

That said, the following are in scope for responsible disclosure:

- Dependency vulnerabilities in `requirements.txt` packages
- Issues in the benchmark runner that could produce falsified results
  (integrity of the research output is a security concern in this context)
- Any path traversal or arbitrary file write in the profiler or benchmark
  runner when processing external input

## Out of Scope

- The simulation kernel (`src/core/`, `src/mvw/`) — it processes no
  external input and has no network access
- Performance issues (these are research questions, not vulnerabilities)
- The LaTeX paper source

## Reporting

Do not open a public GitHub Issue for security concerns.

Email: aldrich.wooden@snhu.edu  
Subject line: `[holodeck-serial] Security`

Include:
- Description of the issue
- Steps to reproduce
- Potential impact
- Suggested remediation if known

Expected response time: 72 hours.
