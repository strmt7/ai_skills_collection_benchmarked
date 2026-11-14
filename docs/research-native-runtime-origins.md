# Runtime origins and evaluation controls

The native Python controls found three distinct behaviors in the pinned image.
A normal lookup resolved Packaging to the captured project. Isolated Python
resolved it to the image's installed Packaging copy. A project helper named
`pytest.py` could take precedence over the test framework. These mechanisms
follow the documented effects of the working directory, `PYTHONPATH` and
isolated mode. [Python command-line reference](https://docs.python.org/3.12/using/cmdline.html)

The schema-2 grading profile now freezes expected framework and project import
origins. It compares image modules with their pinned paths and hashes, and
project modules with the submitted capture's file identities before tests run.
The Packaging profile explicitly enables Python safe-path behavior and
retains its declared source path.

| Controller control | Observed result |
| --- | --- |
| Complete two-file edit | 11/11 |
| Unchanged captured source | 0/11 |
| Edit with a root-level `pytest.py` helper | 11/11 using the image's pytest |
| Helper on the explicit source import path | Origin mismatch, score withheld |
| Failed or interrupted collection | No grading containers opened, score withheld |

The import settings form part of this local experimental profile. The original
publisher verifier and score mapper retain their measured code revisions.
Origin checks cover the declared modules at startup. Transitive imports and
later import changes need further qualification before broader claims.
An unresolved import conflict remains visible in the attempt records and
requires diagnosis before complete model comparisons can be reported.
[Native evidence](../artifacts/research/2026-11-11/evaluation-runtime-origins/review.json)

The updated [evaluation overlay](../included/improved/skills/eval-harness-integrity/SKILL.md)
adds unchanged-input headroom checks, resolved-code verification and complete
attempt accounting. Detailed grader-admission guidance loads through its
supporting reference. The original mirror and earlier overlay versions are
preserved. The overlay remains experimental and unbenchmarked.
