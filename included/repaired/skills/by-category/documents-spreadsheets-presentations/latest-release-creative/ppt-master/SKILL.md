---
name: ppt-master
description: Create and edit slide presentations with PPT Master, using a source-verified SVG editor repair when moving text.
---

# PPT Master SVG editor repair

Before repository work, apply the mandatory agent tools in `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Read the original presentation workflow at `included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master/SKILL.md`. Its exact text is preserved in this overlay under `provenance/original.SKILL.md`.

When using the SVG editor to move text, prepare a separate repaired copy from the repository root. The destination must be a new directory whose parent already exists:

```sh
python included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master/scripts/prepare_ppt_master.py --repo . --destination <new-skill-directory>
```

Use the prepared copy's `SKILL.md` and scripts. Preparation verifies the complete source tree and the repair, retains the upstream attribution, and refuses existing destinations or a changed source lock. This repair is qualified for the pinned v6.6.0 source; requalify it before applying it to another release. The original mirror and its scanner findings remain unchanged.
