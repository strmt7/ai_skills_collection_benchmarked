# Retired Gemini model in skill instructions

Google's [release notes](https://ai.google.dev/gemini-api/docs/changelog#06-01-2026)
state that `gemini-2.0-flash` was shut down on June 1, 2026. Eight pinned
OpenDirectory skills hardcode that model in a Gemini API call: Claude MD
Generator, Meeting Brief Generator, Noise2Blog, Outreach Sequence Builder,
Product Hunt Launch Kit, Reddit ICP Monitor, Reddit Post Engine and Show HN
Writer. Following those calls as written targets a model Google has retired.
Newsletter Digest also mentions the retired model, but its instruction permits
the latest available model as an alternative.

At the inspected upstream commit
[`caac7cda`](https://github.com/Varnan-Tech/opendirectory/tree/caac7cda5621e289591e4e74b400e66ac72ad25b/skills),
seven of the eight hardcoded-call skills still contain those calls. The newer
Show HN Writer no longer mentions `gemini-2.0-flash`; this observation does not
qualify its complete workflow. Newsletter Digest still mentions the model and
the alternative. The locked catalog remains unchanged pending a full source
update review. Select a currently supported model only after checking the
provider's current documentation and the skill's other requirements; these
checks do not establish that any replacement works with the whole skill.

The [source evidence](../artifacts/research/2026-10-30/gemini-retirement/source-evidence.json)
records the pinned and observed upstream commits, file identities and the
native official-page capture digest. The [inventory control](../artifacts/research/2026-10-30/gemini-retirement/reproduce.py)
verifies those source hashes and counts the model references. Its
[Windows](../artifacts/research/2026-10-30/gemini-retirement/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/gemini-retirement/linux-result.json)
results match. The control made no model API calls and did not score an agent;
an altered upstream file was rejected.

To reproduce, obtain the nine current `SKILL.md` files at the recorded commit,
save each as `<skill-name>.md` in a directory, then run from the catalog root:

```text
python artifacts/research/2026-10-30/gemini-retirement/reproduce.py --manifest artifacts/research/2026-10-30/gemini-retirement/source-evidence.json --root . --current-dir <directory>
```

Google's page was read with the isolated Crawl4AI provider
`0.9.5+catalog.portable4`; its native capture returned HTTP 200 and has SHA-256
`9068b8fcec25b59f60d53de5bae2c0e54128e3d5620e6f439e50ebe14ee4313a`.
