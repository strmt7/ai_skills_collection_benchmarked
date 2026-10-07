# Offline text review

`scripts/build_skill_review.py` uses only Python's standard library. Input is a
UTF-8 JSON array containing exactly `id`, `prompt`, `output_text` string fields
per run. IDs must be unique and nonblank, at most 128 characters. Each field has
a 65,536-character bound; the whole input is at most 2 MiB and 100 runs. Empty
output text remains reviewable. Duplicate JSON keys are rejected.

The helper creates a new deterministic HTML file and refuses overwrites.
`--check` compares an existing file with the same input without rewriting it.
Candidate text is escaped, and the content security policy permits only the
fixed script/style hashes. The page uses no remote dependencies, provider,
server, automatic output execution or port/process manipulation.

Verdicts start as `pending`; select `acceptable` or `needs_change` explicitly.
Export downloads `feedback.json`. Each record retains the exact run ID and
feedback, a verdict, and a `reviewed` boolean. Overall status becomes `complete`
only when every run has an explicit verdict. This records human feedback, not
automated correctness, token usage or benchmark scores.

Actual Chromium controls verify hostile script-boundary text stays literal,
quoted IDs and multiline feedback survive export, partial reviews stay pending,
and all explicit verdicts enable completion. The helper has twelve Python tests
covering input bounds, ambiguous JSON, active markup, collisions and freshness.
These limited controls do not certify every browser or binary output viewer.
