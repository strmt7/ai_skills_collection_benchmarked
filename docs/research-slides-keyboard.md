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
