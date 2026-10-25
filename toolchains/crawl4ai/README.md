# Crawl4AI research-provider source build

This identifies an explicit downstream build, **0.9.5+catalog.portable4**, from
the latest non-prerelease Crawl4AI release checked on 25 October 2026 (0.9.5).
Upstream classifies it as beta. It is not an official upstream release.

The adaptation fixes Windows no-follow downloads, a conflicting `fit_html`
property that breaks native failure JSON, and an automation-hiding browser flag
that was active even with `enable_stealth=False`. Original upstream archives and
catalog skill mirrors remain unchanged. The download helper has an explicit
Apache-2.0 license from its pinned source; its copyright, full license and source
URL are preserved in `vendor/`, `source.json` and `CATALOG_BUILD_NOTICE.txt`.
Every modified upstream file also carries its own change notice. Earlier
portable3 source pins and native results remain recorded separately.

## Reproduction and checks

The [native CI workflow](../../.github/workflows/crawl4ai-provider.yml) downloads
the exact sdist, prepares two independent adaptations, installs the complete
hashed build graph normally, and requires both wheels to match the qualified
SHA-256 in `source.json`. No post-install source patching is used. The workflow
then installs complete original and repaired dependency graphs normally, runs
`pip check`, verifies all 87 repaired runtime source files, and uploads results
from the same 20 native consumer controls against each package. Original
failures are retained as measurements; repaired failures fail the workflow.

`prepare_crawl4ai_source.py` accepts an existing archive and a new workspace
`.venv` stage, or `--check` to verify a stage without replacing it.
`verify_crawl4ai_wheel.py` admits exact wheel bytes and generates a local install
lock replacing only the original Crawl4AI record. The version-controlled
`requirements.txt` retains public upstream coordinates for advisory services.
All runtime, build and bootstrap records are audited and tracked by Dependabot.
These are Windows x64 CPython 3.13.17 locks, not universal dependency graphs.
Paths are resolved from the current checkout and explicit stage arguments.
The tools require no fixed drive, user account, global package installation,
browser profile, MCP registration or particular AI agent. Windows is the
qualified operating-system target for this provider.

The current major upgrades proposed in Dependabot PRs 29–31 are incompatible:
Patchright 1.64.3 requires `pyee<15,>=13`; Crawl4AI 0.9.5 requires
`xxhash~=3.4` and `snowballstemmer~=2.2`. Normal pip dry runs on each exact PR
lock return `ResolutionImpossible`. Keep the newest compatible releases until
upstream supports a newer graph and native qualification passes. No dependency
ignore rule or advisory exclusion is added. The [resolver review](../../artifacts/research/2026-10-25/crawl4ai-dependency-pr-review.json)
records exact PR heads, lock digests and native failure evidence.

**Build isolation matters:** upstream `setup.py` clears the cache under
`CRAWL4_AI_BASE_DIRECTORY`, a different spelling from `CRAWL4AI_BASE_DIRECTORY`.
Do not build against a personal profile or shared cache. CI confines both to a
new job-owned tree and verifies that a separate profile cache survives.
The preparation tool does not execute source, install packages or modify a
provider. Building wheels executes reviewed upstream/build-tool code.

## Research policy and limits

Browser research still requires the [mandatory tool policy](../../docs/agent-tools.md),
an isolated admitted runtime and actual native crawl receipts. The 20 CI controls
launch no browser and qualify no external page. Separate local qualification
also exercised eight actual headless-browser controls and nine NLTK controls,
and three official pages were captured with the repaired provider. These local
records do not constitute hosted cross-platform qualification.

Strict research uses robots checks, TLS verification, Chromium sandbox opt-in,
`enable_stealth=False`, an identifying user agent, no personal/persistent profile,
no external LLM, no retry or fallback, and bounded deadlines. A live check must
show `navigator.webdriver === true` and no automation-hiding flags. Setting a
configuration boolean alone did not establish this in the unmodified package.
Do not launch the optional stealth mode during research; CI only checks its
argument-generation contract.

Full `CrawlResult.model_json_schema()` remains unsupported for the arbitrary
`SSLCertificate` type. The native evaluator records that separate capability
failure. Valid result and failure JSON are supported by the repaired contracts.
Component controls measure provider behavior; they do not measure coding-agent
efficacy or establish an advantage over an unskilled agent.

This product includes software developed by UncleCode (https://x.com/unclecode)
as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai).
