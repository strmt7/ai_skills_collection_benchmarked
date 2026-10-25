# Toolchain maintenance

The October 25, 2026 update resolves both Python dependency graphs afresh with
pip-tools 7.6.2, installs them together with hash checking in a new isolated
environment, and verifies their dependency compatibility. The retained
[audit](../artifacts/research/2026-10-25/python-dependency-audit.json) reports no
known vulnerabilities across its 58 dependency records. This does not cover npm
graphs, historical secret findings or source-code vulnerabilities.

The validation lock now selects certifi 2026.10.23, filelock 4.2.4, setuptools
84.2.1 and Ruff 0.17.2. The report lock selects Pillow 13.0.0. These versions
include fixes beyond the minimum releases requested by the outstanding bot PRs.
The report dependencies previously escaped the job labeled "all extras"; CI now
audits both graphs and checks each against its actual project extras.

Regenerate a graph in its intended interpreter and operating system, then verify
the existing pins without upgrading them:

```sh
python -m piptools compile --upgrade --generate-hashes --allow-unsafe --no-emit-index-url --no-emit-trusted-host --extra=test --extra=lint --extra=security --output-file=requirements-lock.txt pyproject.toml
python -m piptools compile --upgrade --generate-hashes --allow-unsafe --no-emit-index-url --no-emit-trusted-host --extra=reports --output-file=requirements-reports-lock.txt pyproject.toml
python tools/verify_dependency_lock.py --json
python tools/verify_dependency_lock.py --lock requirements-reports-lock.txt --extra reports --json
pip-audit --strict --requirement requirements-lock.txt --requirement requirements-reports-lock.txt
```

The current locks were resolved and installed on Windows with CPython 3.14.8.
They are not universal lockfiles. CI uses the supported Python release lines,
including the newly available 3.13.17 and 3.14.9 patches. Hosted acceptance must
be checked against the exact pushed commit.

GitHub Actions use full commit pins, resolved from all published stable release
pages by [the release auditor](../tools/audit_workflow_versions.py). This update
selects setup-python 7.1.0 and CodeQL Action 4.39.1. A release lookup proves
version provenance; successful execution is a separate requirement.

The current FlitzZip integrations were inspected as a source of general
engineering practices: bounded source windows, explicit unread ranges,
source-bound query receipts, isolated CPU indexes, and dependency plus consumer
qualification. This repository retains its own stricter
[mandatory-tool policy](agent-tools.md), including the prohibition on replacing
Crawl4AI with another page reader. No other repository was modified.

The release review also found Caveman 4.0.1, Crawl4AI 0.9.5 and CocoIndex 1.0.26.
Their release numbers do not qualify their runtimes here. The local Caveman
overlay remains internal-only; the inspected upstream runtime adds hooks,
proxying and synchronization that this overlay does not require. The retained
research used the reviewed Crawl4AI 0.9.4 portable source build and CocoIndex
Code 0.2.42 with CocoIndex 1.0.25. New runtime cohorts require isolated admission
and real consumer checks before being represented as qualified.

These are dependency and evidence improvements. They do not establish that
skills outperform an agent without skills or instructions. That requires
independently defined coding tasks, matched resources, retained agent outputs,
and measured quality, cost and regressions.
