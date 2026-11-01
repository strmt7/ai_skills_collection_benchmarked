---
name: ckm-design-local-search
description: Search the pinned design skill's logo and corporate identity datasets with explicit errors and optional English query expansion.
---

# Design data search

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

This overlay replaces only local logo and corporate identity dataset searches. For design guidance and other functions, read the [original skill](../../../../../../skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design/SKILL.md); its original text is also in `provenance/original.SKILL.md`. The original brief generator, image generation and HTML renderer are unchanged and have not been qualified by this repair.

Use Python 3.11–3.14. In an isolated environment, install the pinned wheel with `python -m pip install --only-binary=:all: --require-hashes -r requirements.txt` from this overlay directory. Then run, for example:

```bash
python scripts/search.py --collection cip --domain deliverable "uniforms"
python scripts/search.py --collection logo --domain style "minimalist"
```

Logo domains are `style`, `color` and `industry`; corporate identity (`cip`) domains are `deliverable`, `style`, `industry` and `mockup`. The CLI differs from the original search scripts. `--max-results` accepts 1–50; `--data-dir` points to a replacement data root containing the `logo` and `cip` directories.

Results are JSON. Exit 0 denotes a completed search, including a search with no matches; errors return JSON with `ok: false` and exit 2. Check `count`, `matched_terms` and `query_terms` before relying on a result: partial matches are possible. The default `--match auto` uses exact terms when a record contains all query terms, and otherwise tries English Snowball stemming. `--match exact` disables expansion; `--match expanded` always tries it. `matching` records the chosen mode and `used_stemming` identifies individual results that needed expansion. English stemming is heuristic and can introduce irrelevant matches or miss relevant ones. Other scripts and non-English morphology are not evaluated. Expanded searches require the pinned `snowballstemmer` package; exact searches can run without it.

Run `python -m unittest discover -s . -p 'test_search*.py'` from the overlay directory to check the independent synthetic controls and bundled-data cases. These controls establish selected search behavior, not design quality or improvement in agent performance. The expansion package is the separately installed BSD-licensed [Snowball stemmer](https://pypi.org/project/snowballstemmer/3.1.1/).
