# Stable-version review, 2 October 2026

Primary GitHub release APIs were queried across all release pages for the five
Actions used in this repository. Drafts, prereleases, and non-action bundle tags
were excluded. The initial 19 invocations used full immutable commit hashes;
the added report and live-audit jobs bring the verified current total to 24:

| Action | Stable version |
| --- | --- |
| actions/checkout | 7.0.1 |
| actions/setup-python | 7.0.0 |
| actions/upload-artifact | 7.0.1 |
| github/codeql-action | 4.38.2 |
| softprops/action-gh-release | 3.0.3 |

Release notes, resolved commits, original inventory, and action manifests are
recorded under `artifacts/research/2026-10-02/workflow-*.json`. Every current
workflow input is accepted by the selected action manifest; all selected actions
use Node 24. Hosted CI execution remains required. Gitleaks 8.30.1 remains the
latest stable release at this observation.

The official [Python 3.14.8 release](https://www.python.org/downloads/release/python-3148/)
is dated 30 September 2026 and includes expedited security fixes. The official
[release announcement](https://discuss.python.org/t/python-3-10-22-3-11-17-3-12-15-3-13-16-and-3-14-8-are-now-available/109296)
also declares Python 3.10 end of life. Python 3.14.8 was provisioned from the
official full-runtime ZIP with manifest and archive SHA-256 verification. A
parent-virtual-environment setup failure was recorded and repaired before
qualification. A separate Python 3.14.8 environment installed the hashed lock,
passed lint and type checks, and ran 271 tests successfully with one documented
NTFS/POSIX executable-bit skip. Seeded lock consistency also passes. This is
local Windows evidence; hosted CI across other platforms remains pending.
Production CI jobs now select 3.14.8. Compatibility lanes select supported
3.11.17, 3.12.15, 3.13.16, and 3.14.8 releases; their Linux and current Windows
availability was checked in the official Actions Python version manifest.
The Python minimum is now 3.11. Frozen agent experiments preserve their 3.12.14 interpreter until
the entire matched block finishes; a runtime change requires a new protocol and
new matched comparisons.

The official [Node download page](https://nodejs.org/en/download/current) lists
26.10.0 as Current and 24.21.0 as latest LTS. The staged image-CLI checks used
24.15.0 and require repetition on the selected supported current runtime. A
latest-release claim is separate from an LTS claim.

Node 26.10.0 is now provisioned from the official Windows ZIP with SHA-256
verification. Its executable has a valid OpenJS Foundation Authenticode
signature. The bundled npm 11.19.1 lagged the registry's current stable 12.2.0;
12.2.0 was installed under an isolated workspace prefix, its declared Node
engine range checked, and its actual version verified. The staged image CLI
again passes all four real conversion/fallback checks on Node 26.10.0.
`node-runtime-qualification.json` records these identities, hashes and endpoints.
No system installation, registry settings or persistent PATH was changed.

The report extra uses current stable Matplotlib 3.11.2, verified against PyPI,
with a separate hashed report lock. It produces standalone SVG and PNG charts
from verified matched trials. The original comparison runtime remains available
for replay; current production tooling uses the qualified Python 3.14.8 runtime.

Remaining audit scope includes Python and npm dependency registries, local
development executables, scanner binaries, workflow runtime versions, upstream
skill helpers and their dependency files, adapters, and instructions against
current official documentation. No repository-wide freshness claim is made.
