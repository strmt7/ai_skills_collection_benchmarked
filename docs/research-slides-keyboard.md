# Keyboard and chart behavior in HTML slides

Use the [maintained slides template](../included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-slides/SKILL.md)
for keyboard navigation, reduced-motion support and scrollable long slides.
Localize the default labels and check the complete deck on the devices used
for presenting. For a deck that must open without internet access, use a local
copy of its pinned Chart.js bundle.

## Original keyboard behavior

The pinned `ckm:slides` skill includes an HTML slide template whose global
Space-key handler also runs when a navigation button has focus. In a three-slide
fixture based on that template, pressing Space on the focused previous button
from slide 2 advanced to slide 3. Clicking the same button or pressing Enter
returned to slide 1. The [W3C button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/)
expects Space and Enter to activate a focused button.

The [reproducer](../artifacts/research/2026-11-01/slides-keyboard-control/reproduce.cjs)
extracts the template's first HTML block, adds two ordinary slides and blocks
its external Chart.js request. Its diagnostic variant leaves the Space shortcut
alone when a button has focus: in this limited control, Space then activated the
previous button and still advanced from an unfocused page. This variant is a
causality check, not a complete accessibility repair. Inputs, other interactive
controls, assistive technologies, full-deck appearance and agent behavior were
not assessed.

The result occurred with Playwright 1.64.1 on Windows at a 1280 × 720 viewport,
using Edge 156.0.4314.58 and Chrome 156.0.8078.80 under Node
[24.22.2](../artifacts/research/2026-11-01/slides-keyboard-control/node-24.22.2-edge.json)
and [26.13.0](../artifacts/research/2026-11-01/slides-keyboard-control/node-26.13.0-edge.json).
The corresponding Chrome receipts are available for
[Node 24](../artifacts/research/2026-11-01/slides-keyboard-control/node-24.22.2-chrome.json)
and [Node 26](../artifacts/research/2026-11-01/slides-keyboard-control/node-26.13.0-chrome.json).
Both browsers are Chromium-based; this does not establish behavior in other
engines or versions.

The mirrored template is source-locked at commit
`07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4`. The same template Git blob
`8b5a178f6c28c3bacc4f411c587c1495a48c778c` was retrieved at upstream main
`3a13158ff1f32156cbe144108de48eda2ecaed9a`, observed on 1 November 2026.
The upstream entrypoint changed, so this is not a claim that the whole skill is
unchanged. The control normalizes CRLF to LF and requires template SHA-256
`fd5b051a37365fc6059c75bb388ec6f64daf1bd9ae938b287b6d762dc83c0c35`;
a changed input was rejected. The original mirror is unchanged.

The W3C page was read using the isolated Crawl4AI provider
`0.9.5+catalog.portable4`; its retained native result SHA-256 is
`6811910810a57f9efffdbba9f4b2972bf1297ad1a950bfd21e92be25f6e46b7c`.
This component observation is not an agent benchmark or proof of a skill advantage.


## Maintained template

The separate [slides overlay](../included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-slides/SKILL.md)
retains the original skill and template in its provenance directory. Its
template keeps the focused previous button's Space activation, avoids the tested
keyboard and pointer shortcuts on interactive content, and makes overflowing
slide regions focusable and scrollable. Pointer advancement is limited to the
slide background. Authors should localize the default English labels and test
their complete deck. A slide may initially overlap fixed controls in a short
viewport; the tested content can be scrolled above them.

The template also disables its tested transitions and animation classes when
`prefers-reduced-motion: reduce` is active. The upstream `animate-count` example
still references an undefined `countUp` keyframe; the overlay does not claim to
implement a counting animation. The [W3C explanation of animation from
interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions)
describes reduced-motion preferences as one technique. Its reviewed Crawl4AI
result has SHA-256
`552c15d201223507e977fbbeffa4251fa3cb6c93b5f259d734095bc64e6febb1`.

The template uses Chart.js 4.6.2. Its exact package bundle rendered the four
expected values in the line example. The 72 browser controls exercised keyboard,
pointer, touch, overflow, reduced motion, labels and chart rendering with
Playwright 1.65.1 and Node 24.22.3 and 26.13.1. The matrix covers Chromium and
WebKit on Windows and Chromium and Firefox on Linux. The scope is the named
fixtures and interactions. [Current evidence](../artifacts/repaired-skill-readiness/slides-navigation-v1/qualification.json)

## Reproduce the current controls

On Windows, use the managed development frontend and pass the path to one of
the qualified Node executables. The runner fetches and verifies the pinned pnpm release asset,
installs the exact frozen graph and provisions the two required browser engines.
It writes a receipt for each check and uses a disposable cache by default.

```powershell
./dev.ps1 python artifacts/repaired-skill-readiness/slides-navigation-v1/reproduce.py --node $node --output .venv/slides-results
```

Use `--cache-root` with `--prepare-only` to provision a caller-owned cache,
then `--offline` with the same cache to exercise the already provisioned
dependencies. The hosted workflow runs that sequence on both platforms and
uploads the preparation and control receipts. [Workflow](../.github/workflows/slides-navigation.yml) [pnpm frozen install](https://pnpm.io/cli/install) [Playwright browser installation](https://playwright.dev/docs/browsers)

The runner pins pnpm 12.23.0 by version and verifies the publisher's native
archive. The application lock uses pnpm's single-document format so GitHub can
read the dependency graph. Both supported platforms resolved the same graph.
[GitHub dependency graph support](https://docs.github.com/en/code-security/reference/supply-chain-security/dependency-graph-supported-package-ecosystems)

The prior Node, Playwright and Chart.js controls remain available under their
original Git revision. [Prior qualification](https://github.com/strmt7/ai_skills_collection_benchmarked/blob/a9552b3ef07ed2490134f255b8ad1ca87b54525a/artifacts/repaired-skill-readiness/slides-navigation-v1/qualification.json)
