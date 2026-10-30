# Infographic export component review

The pinned [Create Infographics skill](../included/skills/by-category/documents-spreadsheets-presentations/creative-reference/create-infographics/SKILL.md)
includes an exporter for PNG, PDF and SVG. On the tested Windows host, when
neither Inkscape nor `pdf2svg` was on the controlled executable path, the
exporter reported that SVG export was skipped. With UTF-8 output enabled,
both `--format svg` and `--format all` nevertheless exited successfully without
creating an SVG; `all` also listed the missing SVG as exported. Check the
requested output files rather than relying on the exit status or final list.

In the host's default `cp1252` output configuration, the `all` run instead
raised a `UnicodeEncodeError` while printing the missing-converter guidance.
Both configurations produced PNG and PDF files with the expected file
signatures before the SVG step. These checks do not establish rendering quality
or that a real SVG converter works.

The [source-bound control](../artifacts/research/2026-10-30/infographic-export/reproduce.py)
used a local synthetic page, the exporter's documented `--no-serve` mode, a
disposable working directory and a controlled path without either converter.
It ran real Chromium exports with Windows Python 3.13.17 and Playwright
[1.62.0](../artifacts/research/2026-10-30/infographic-export/windows-result.json)
and [1.64.1](../artifacts/research/2026-10-30/infographic-export/windows-latest-result.json).
The latter used its matching Chromium 156.0.8078.4 in a separate environment;
the [PyPI package API](https://pypi.org/pypi/playwright/json) reported 1.64.1
as the latest release when checked. An altered exporter was rejected by the
source check. No preview server, external page or agent benchmark was run.

The repository now resolves to `aizzaku/aiz-infographic`. At the inspected
upstream commit [`8054906f`](https://github.com/aizzaku/aiz-infographic/blob/8054906f52c2b499d39ea108f55d2ab5a171e25e/scripts/export.py),
the exporter differs and its [CLI help](../artifacts/research/2026-10-30/infographic-export/current-help.txt)
describes PNG export only. That observation does not qualify an upstream
upgrade or prove equivalent PDF and SVG support. The [source evidence](../artifacts/research/2026-10-30/infographic-export/source-evidence.json)
records the observed identities; the source mirror remains unchanged.

To reproduce the control on Windows, install Playwright and its matching
Chromium in an isolated environment, create a private scratch directory, and
run from the catalog root:

```text
python artifacts/research/2026-10-30/infographic-export/reproduce.py --root . --scratch <directory>
```
