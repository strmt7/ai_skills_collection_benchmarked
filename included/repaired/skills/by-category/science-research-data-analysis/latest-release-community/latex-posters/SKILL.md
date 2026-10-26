---
name: latex-posters
description: Review a research poster PDF with a maintained, read-only Poppler preflight while preserving the locked original skill.
---

# Poster preflight repair

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

For poster design and scientific content, read the original skill at `included/skills/by-category/science-research-data-analysis/latest-release-community/latex-posters/SKILL.md`. Its exact text is also preserved in this overlay under `provenance/original.SKILL.md`.

For PDF preflight, use this overlay's `scripts/review_poster.sh`, not the original mirror's review script or its inline example. Run it with Bash and the PDF path. Poppler's `pdfinfo`, `pdffonts`, and `pdfimages` must be available on `PATH`.

Exit 0 means automated checks passed, exit 1 means a check failed, and exit 2 means a required inspector is unavailable. Inspector warnings are retained. Page dimensions, font embedding, and image resolution do not establish scientific correctness, visual quality, or printer acceptance; complete manual review.
