# Slide-template keyboard control

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

To reproduce, install the exact Playwright version in an isolated project using
the existing [Playwright repair lock](../included/repaired/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill/package-lock.json).
Run `node` on the reproducer with three arguments: the absolute path to the
installed `playwright` module, the mirrored `references/html-template.md` path,
and the absolute path to a Chromium-compatible browser executable. The recorded
versions are a tested configuration, not a guarantee for other environments.

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

The template uses Chart.js 4.6.1. The exact package bundle rendered the line
example's four expected values in the tested browser configurations; the CDN
still requires network access unless a local copy is supplied. The component
[controls and native results](../artifacts/repaired-skill-readiness/slides-navigation-v1/qualification.json)
cover Chromium and WebKit on Windows and Chromium and Firefox on Linux, with
Node 24.22.2 and 26.13.0. They exercise keyboard, pointer, touch, long-content
scrolling, reduced motion, labels, and chart rendering in specified fixtures.
Linux WebKit was not tested because its system libraries were unavailable;
WebKit was exercised on Windows. These controls are not a full accessibility
or assistive-technology audit, interactive chart test, model benchmark, or proof
that the skill improves agent performance.

The [workflow](../.github/workflows/slides-navigation.yml) installs pinned npm,
Playwright and Chart.js dependencies in temporary directories, runs the same
controls on the four hosted configurations, and uploads the individual JSON
results. Its browser installations are isolated to the job. The scripts also
accept explicit paths to installed dependencies and the two template files.
