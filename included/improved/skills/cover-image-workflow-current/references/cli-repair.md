# Source-locked CLI acceptance repair

This is a bounded repair of the historical CLI's credential display, QA result
schema, retry exhaustion, output replacement and logo download behavior, with
a current locked dependency graph. Prefer an available
qualified image tool for real generation. The repair retains the historical
provider configuration and plaintext configuration storage; it does not qualify
those choices for production or authorize credential persistence.

From the collection root, prepare a new package without changing the mirror:

```sh
python included/improved/skills/cover-image-workflow-current/scripts/prepare_cli.py \
  --source included/skills/by-category/creative-media-design/reddit-verified-gtm-registry/blog-cover-image-cli \
  --output /absolute/path/to/new-stage
```

The preparer checks all 20 source files against `source-files.json`, including
the declared October 25 advisory graph. It accepts portable text newlines and
requires exact binary bytes. It rejects source drift, linked inputs, incomplete
packages, overlapping paths and an existing destination. It copies the checked
bytes, replaces three JavaScript files and both dependency declarations, and writes a preparation
receipt. It installs nothing and makes no provider request. Preserve a failed
partial stage for diagnosis; select a new output for a new attempt.

To reproduce the component controls, use the qualified Node 26.12.1/npm 12.2.1
cohort and the staged lock:

```sh
npm ci --ignore-scripts --prefix /absolute/path/to/new-stage
npm audit --prefix /absolute/path/to/new-stage
node benchmarks/dependency-regressions/image_cli_acceptance_controls.mjs \
  --package-root /absolute/path/to/new-stage --output /absolute/path/to/new-report.json
node benchmarks/dependency-regressions/image_logo_resource_controls.mjs \
  --package-root /absolute/path/to/new-stage --output /absolute/path/to/new-logo-report.json
```

The controls intercept provider responses and isolate configuration; they do not
perform real image generation. Before any real request, qualify stable provider
models, supported request fields and output image decoding as
described in the main skill. Do not pass a real credential to the historical
`set-key` command: its argument and plaintext storage contracts are retained.

In this repair, getters report only `[configured]`. Invalid QA schemas and
exhausted retries fail before writing an image. Accepted output uses exclusive
creation by default; `--overwrite` explicitly permits replacement. A successful
model critic is still insufficient evidence of actual image fidelity. Read the
collection's `docs/research-image-cli-acceptance.md` for measured component
results and their limits; no coding-agent advantage has been established.

Logo downloads now share a ten-second deadline and at most three redirects
across the three possible providers (at most six fetch calls). Each response
and converted PNG is limited to 4 MiB; decoding admits at most 16,777,216 pixels
and one page. Streams rejected by the byte limit are cancelled. A direct URL
may use HTTP or HTTPS and must not embed credentials. Bare domain inputs cannot
inject paths or query parameters; the Brandfetch client identifier is encoded.
Failures return no logo and report a constant message without raw URL/error
values. The deadline governs network work; pixel/output caps bound decoding,
which is not a hard CPU-time or process-isolation guarantee.

The collection's `docs/research-image-cli-resources.md` records the current graph,
all resource reviews and identical original/repaired control results. Consult
the [current qualification record](qualification-2026-10-25.md) for provider and
publishing limits. Do not activate the archival source publishing workflow.
