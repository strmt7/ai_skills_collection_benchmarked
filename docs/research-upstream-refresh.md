# Upstream source review, October 25, 2026

The [availability snapshot](../artifacts/research/2026-10-25/upstream-source-availability.json)
checked all 30 locked repositories through native GitHub APIs: eight matched
their selected release or default-branch revision, 20 had updates, and two
EvoLinkAI endpoints returned HTTP 404. A 404 does not establish whether a source
was removed, renamed or made private. The report preserves errors and native
capture digests. Release metadata and path counts do not approve source contents
or licenses. A null API license field means unknown.

One of those 20 updates is applied here: `lackeyjb/playwright-skill` v5.0.0,
commit `289abdea7df857dc7a6ece937dbe0c5ecc964ccd`. The other 672 catalog records
and 29 source locks are unchanged. Its upstream frontmatter changes the generated
installation name from `playwright-browser-automation` to `playwright-skill`.
The original mirror is regenerated from that pin; its instructions are not
rewritten to resolve findings. The exact MIT [copyright and permission notice](../artifacts/source-notices/lackeyjb-playwright-skill/289abdea7df857dc7a6ece937dbe0c5ecc964ccd/LICENSE)
is preserved as source bytes, bound to the commit and checked by the generator
against its native Git object. Offline validators reject notice drift.

The [package review](../artifacts/research/2026-10-25/playwright-v5-source-review.json)
records all six mirrored resources, 24 upstream files verified against Git
objects, and native Windows checks. With Node 26.12.1, npm 12.2.1 and a separate
Playwright 1.64.1 consumer installation, all 12 unchanged upstream tests passed.
A real local browser check exercised the cookie helper, accessible locators and
login redirect. Automation remained disclosed; Chromium sandboxing was explicitly
requested. This check does not independently attest every browser subprocess flag.
The harness allowed only its own HTTP listener, blocked ten other development-port
probes before transport, and checked temporary deletion scope. An initial harness
path-quoting failure is retained separately from the successful retry.

Both the retained upstream lock and separate consumer graph returned zero known
npm advisories. The source lock still contains Playwright 1.62.1; the latest SDK
was tested separately without silently rewriting the source. The source retains
fixed `/tmp` and agent-specific paths, conflicting legacy locator/Actions examples,
fixed context locale/timezone defaults, and potentially sensitive header parse
diagnostics. Those findings keep research in progress. These native checks do not
measure coding-agent effectiveness, external-site behavior or superiority.

The initial full suite exposed historical evidence incorrectly tied to the latest
catalog pin. The [source-history registry](../data/catalog_source_history.json)
now preserves the old catalog entry and exact original skill bytes from published
commit `8aec4c3c127cb8a3d2a9b24627445b89fe2a2242`. This records the source identity
observed there; it does not reconstruct the original benchmark session or archive
the complete old package. The old license was separately captured at its source
commit. The April failure and repair retain their exact original artifacts.
Validation checks the registered version and snapshot hashes; the per-skill count
for v5 excludes the old runtime artifact. Repair regeneration refuses a stale
failure before cleanup can run. Historical evidence remains visible in the dated
report and cannot qualify a new source pin.

Nineteen observed source updates still require admission and review. In particular,
the old K-Dense and Varnan selection prefixes have no skill paths at the observed
new revisions. Their changed layouts require investigation before catalog changes;
an empty old prefix is not evidence that the skills should be deleted. The
Crawl4AI provider remains qualified for Windows x64. Host independence introduces
no additional operating-system target.
