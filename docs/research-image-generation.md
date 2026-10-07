# Image-generation package research

Reviewed the historical OpenDirectory blog-cover-image-cli entrypoint and its
complete 20-resource package: 12 text/configuration/code files and eight image
examples. Text includes the complete CLI, three helpers, license, README,
workflow and package graph. Binary resources were consumed as example inputs;
visual aesthetic/rights assessment beyond the retained ISC notice is not claimed.
Current OpenDirectory moves the skill from `packages/cli/skills/` to `skills/`
and supplies only its entrypoint/README, calling the published CLI externally.
This is one review in progress, not completion of the media category.

## Findings and observations

The historical SKILL.md contains only metadata. The adjacent README claims
guaranteed exact text and successful self-healing, but prompts and model critics
do not establish artifact fidelity. Its referenced `agent-skill/` path is absent.
The actual `bin/cli.js` and eight examples are present in the mirror; the earlier
dependency probe copy was partial and must not be confused with the mirror.

Conf is used without a credential-vault integration/encryption option. API keys
are accepted in command arguments and persisted to its local JSON configuration;
masking output does not make that storage secure. Short keys cause a negative
String.repeat count, and an eight-character key is exposed by the old mask.
After all three QA attempts fail, the CLI still writes the rejected image, prints
Success and exits zero. Its critic parser accepts arbitrary JSON without schema
validation. Its SIGINT handler also exits zero; that observation is source review,
not a qualified cross-platform signal probe.

Logo fetches have no explicit request/body/decode resource limits. Default output
filenames are derived from raw logo input, explicit output overwrites existing
files, and response candidate accesses assume nonempty nested structures. These
need controlled failure/overwrite/schema/network fixtures before a supported
implementation can be described as repaired. No real provider was contacted.

The embedded release workflow uses obsolete action/Node versions and token-based
publishing. It is source material; it was not executed or promoted to root CI.
The README's Node 18 floor conflicts with its own package graph's newer engines.
Its entrypoint and README still recommend preview model identifiers. Google's
[specific model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image)
documents a stable image identifier; the
[deprecation schedule](https://ai.google.dev/gemini-api/docs/deprecations) lists
the old image preview with a June 2026 shutdown date. Current SDK
[ImageConfig](https://googleapis.github.io/js-genai/release_docs/interfaces/types.ImageConfig.html)
has no GenerateContent `numberOfImages` field. Generic guides can lag specific
model lifecycle notices; real availability was not queried with credentials.

## Current dependency and runtime controls

Primary registry observations resolve all nine direct dependencies to current
stable versions, including Google GenAI 2.26.0 and Sharp 0.35.5. A separate complete
package declaration/lock is published under
`benchmarks/dependency-regressions/fixtures/image-cli-current/`. npm 12.2.0 with
Node 26.10.0 installs it; the advisory audit reports zero known findings across
168 dependency records, including optional platform packages. Deprecated-package
warnings remain visible; a zero advisory count is not a vulnerability guarantee.

`tools/prepare_image_cli_controls.py` copies the complete immutable package into
a new workspace stage, preserves source bytes, substitutes only the explicit
control graph, and checks hashes before/after runtime probes. The first provision
failed because sanitizing the copy changed CRLF bytes while provenance expected
raw bytes; its failed log remains. The corrected byte-preserving replay installs
with npm ci and passes post-run provenance checks. Stages are never overwritten.

The public `image_cli_current_controls.mjs` reproduces nine actual controls:
SVG/JPEG conversion dimensions, non-image rejection, all three logo fallbacks,
current Google SDK image/critic response parsing, CLI imports/help, short-key
masking failure and QA failure reported as success. Fetches are intercepted;
child configuration/output lives in a unique temporary fixture without inherited
provider credentials or user profiles. Passing negative controls reproduces the
defects; it does not repair them or establish model availability/aesthetics.
Receipts retain the staged graph/source hashes and earlier partial-copy results.

The catalog generator's partial lockfile field rewrite has been removed. Hashing
and copying must not invent resolutions, downgrade newer packages or disguise
graph bytes. Historical mirrored graphs remain unchanged and their existing
hashes still validate. Reproducing a historical transformed upstream graph uses
its historical generator snapshot; a new source refresh or repair must qualify
and record its complete graph. Known old dependency findings remain findings.

An explicit ISC-licensed `cover-image-workflow-current` overlay implements the
workflow decisions: current tool/model qualification, private credentials,
observable artifact acceptance, bounded attempts and truthful failure status.
Its exact original entrypoint and complete package hashes are retained. It has
not repaired the old CLI, made paid provider calls or established agent gains.

Remaining: independent agent comparisons, actual provider qualification where
authorized, critic-schema/resource/overwrite controls, implementation repairs,
upstream publication changes and the other 29 media skills.
