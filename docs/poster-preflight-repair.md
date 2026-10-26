# Poster preflight repair

The maintained [LaTeX poster overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/latex-posters/SKILL.md) provides a read-only PDF preflight. It keeps the original skill text in `provenance/` and records the original script's hash; the source mirror is unchanged.

From the repository root, run the preflight with Bash and a PDF path:

```bash
bash included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/latex-posters/scripts/review_poster.sh "path/to/poster.pdf"
```

Poppler's `pdfinfo`, `pdffonts`, and `pdfimages` must be available on `PATH`. The script exits with **0** when the automated checks pass, **1** when a check fails, and **2** when required inspectors are unavailable. Warnings and inspector diagnostics remain visible.

The checks cover page count and dimensions, file size, embedded fonts, and raster-image resolution. They do not assess the correctness of the science or replace visual inspection and the printer's requirements. The original scanner findings remain recorded against the unchanged mirror; this overlay does not establish an agent benchmark improvement.
