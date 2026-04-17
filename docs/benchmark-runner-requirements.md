# Benchmark Runner Requirements

This repository defines benchmark scenarios. It does not mark a skill as passed until a separate runner records real artifacts for that skill and scenario.

Required for every benchmark run:

- Record `skill_id`, `scenario_id`, catalog commit, source repository commit, selected ref, runner version, model/runtime identifier, environment, and timestamp.
- Record the immutable dataset, website, source checkout, or workflow snapshot used for scoring.
- Save the agent transcript or command log, files read, files written, output artifact, metric values, and evaluator result.
- Keep synthetic fixtures as supplemental probes only. A synthetic fixture cannot replace the real dataset, website, source checkout, or workflow required by the scenario.
- Mark a runtime claim as passed only when objective checks pass and artifacts are available for review.

Visual parsing and browser skills:

- Test against actual websites or a recorded local mirror of an actual website, plus synthetic pages with known ground truth when useful.
- Save viewport size, screenshot or video evidence, DOM snapshot when available, interaction log, and expected-vs-observed extraction results.
- Include at least one layout change, dynamic state, or adverse condition such as lazy loading, modals, responsive breakpoints, or occluded content.

Context, memory, and retrieval skills:

- Use a long multi-step task with distractor material and delayed recall probes.
- Measure recall precision, missed facts, unsupported facts, and citation/path coverage.
- Record token usage before and after applying the skill. A memory or context-efficiency claim fails if token use increases without a documented quality gain.

Code, DevOps, and security skills:

- Run on real repositories, manifests, logs, or vulnerable fixtures with pinned commits or versions.
- Record commands, exit codes, patches, test results, scanner findings, and regression checks.
- Separate read-only audit results from changes that were actually applied and verified.

Data, science, and document skills:

- Use real public datasets, filings, papers, documents, or spreadsheets with immutable identifiers.
- Record schema assumptions, cleaning decisions, row counts, units, citations, and reproducible analysis commands.
- Validate numeric outputs against an independent calculation or dataset-provided ground truth where possible.
