# Skill-creator package review

Read all eighteen original resources fully: the entrypoint, nine Python files,
three agent role guides, schema reference, two HTML assets, viewer generator and
license. The current Anthropic checkout at
`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4` adds no package resources. Seventeen
files have identical content after the catalog's declared credential/format
normalization; only the license changes. The comparison receipt records both
raw hashes and the exact comparison method. This is a source review, not a
publication or a complete runtime qualification.

The workflow's intent capture, progressive disclosure, realistic near-miss
activation prompts, substantive output checks and analysis of ceiling effects
are useful. Its agent role instructions are source material here: the current
repository requires a single AI session. We launched no model or AI workers.

## Experiment and score defects

The entrypoint drafts assertions while candidate attempts are running, contrary
to this repository's frozen independent-evaluator contract. It also permits a
moving baseline and treats empty feedback as acceptance. The blind comparator
creates its rubric after reading both outputs, prioritizes presentation-weighted
overall ratings above assertions, and discourages ties. Those choices can bias
coding correctness comparisons. Define the rubric first, randomize labels, use
behavioral checks as the primary coding outcome and retain meaningful ties.
The analyzer appropriately warns about superficial assertions but sometimes
describes a small observed difference as clear skill value without uncertainty.

Twelve actual Python controls reproduce:

- An ungraded planned run disappears from the denominator, leaving a reported
  100% rate; the entrypoint's direct `with_skill/grading.json` layout yields no
  aggregated runs because the loader requires `run-*` directories.
- Output characters become token counts. A nonzero embedded duration prevents
  loading actual sibling token usage. Missing values otherwise become zeros.
- A contradicted 150% pass rate is accepted; one actual run is described as three
  repetitions. Metrics trust unvalidated summary fields rather than checks.
- Empty required name/description values pass validation, and the custom parser
  changes YAML literal-block newline semantics.
- Packaging follows a link outside the selected package and includes the owned
  external sentinel. It also overwrites output archives and does not establish
  reproducible ZIP metadata or exclude arbitrary credentials/build products.
- The description loop chooses a winner using repeated reported test scores.
  This is validation selection, not untouched final testing. Duplicate query
  text can move declared test results into training; tiny stratified sets can
  leave no training rows. Description shortening is not revalidated afterward.
- A missing model CLI becomes a passing negative activation case.

The controls run unchanged source files in the pinned Linux/Python 3.14.8 image,
as uid 65534 with network disabled and owned bounded fixtures. The original
process-pool dispatch could not initialize shared semaphores under the backend's
IPC restrictions; both failed receipts remain. The corrected last control adapts
dispatch to native threads while exercising the unchanged query, future error
handling and scoring. Loop selection controls inject deterministic evaluator
results and a fixed proposed description. They test algorithm contracts, not
model behavior, scheduler throughput or skill triggering quality.

The trigger reader also returns after the first tool/assistant activity and can
discard buffered final events when the subprocess exits. It bypasses a nesting
guard, inherits host environment/configuration and terminates only its direct
child. Windows pipe `select` compatibility and real current Claude activation
behavior remain unqualified. These source findings are not counted runtime
passes or evidence about GPT-6.1 Sol.

## Viewer findings and explicit overlay repair

Ten actual Chromium controls reproduce four script-injection paths and two
feedback-state defects, with a normal literal-text control and three repaired
helper controls. All resources outside an owned loopback server are blocked.
Inert local sentinels execute through a prompt closing the embedded script tag,
an unescaped benchmark timestamp, an unescaped grading count, and a quote in an
evidence tooltip attribute. An HTTP 500 feedback response still displays Saved.
Submitting while a second run is unvisited marks both runs complete with empty
feedback. These are reproducible local preview contracts; no real credentials,
external server, provider or model was used.

Other source risks remain: output embedding and recursive discovery follow
links and read unbounded files; the server accepts feedback without origin or
body-size checks; malformed lengths can fail request handling; the launcher
kills arbitrary processes occupying its chosen port. The server binds loopback,
not all interfaces. Font/SheetJS dependencies are remote even in static mode;
the existing SheetJS script does have an integrity attribute. We did not execute
the original port-killing helper, test a live remote attack or certify XLSX/PDF
rendering.

`skill-authoring-current` is an explicit licensed experimental overlay. Its new
offline text-review helper escapes all candidate text, uses a fixed hashed
content security policy, bounds input, rejects ambiguous IDs/JSON and refuses
output collisions. It exports explicit reviewed/verdict states; empty feedback
does not mean approval. It has no server, remote resources, port cleanup or
active candidate embeds. The bundled helper is identical to the tested maintained
tool. Binary/media review, archive repair and real agent comparison remain
separate required qualifications. Agent gains remain unestablished.

## Primary references

- [Agent Skills specification](https://agentskills.io/specification): required
  nonblank fields, progressive disclosure and resource conventions.
- [Anthropic original package](https://github.com/anthropics/skills/tree/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/skill-creator).
- [Current Anthropic package](https://github.com/anthropics/skills/tree/8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4/skills/skill-creator).
- [Python 3.14 futures](https://docs.python.org/3.14/library/concurrent.futures.html):
  process and thread dispatch contracts.

Receipts: `skill-creator-runtime-controls-v3.json` and
`skill-review-browser-runtime-controls-v3.json` under `artifacts/research/2026-10-02/`.
Successful negative controls establish defects, not source readiness or efficacy.
