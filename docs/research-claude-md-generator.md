# Claude instruction generator: source review

The [pinned entrypoint](../included/skills/by-category/coding-refactoring-repository-automation/reddit-verified-gtm-registry/claude-md-generator/SKILL.md)
targets a retired `gemini-2.0-flash` endpoint. The existing
[retirement review](research-retired-gemini-model.md) records Google's 1 June
2026 shutdown announcement and source hashes; no live model request was made.
The source also mandates a file shorter than 100 lines, while its own README
describes a 200-line target. Its audit scoring ranges do not define how to assign
the numerical score, and its bundled evaluation expectations are derived from
the same skill rather than independently specified agent tests.

The current [Claude Code memory documentation](https://code.claude.com/docs/en/memory)
distinguishes project, nested and path-scoped instructions. It recommends
keeping instruction files focused and describes a target below 200 lines, not a
hard universal limit. It states that `@` imports are loaded into context with
the importing file, so placing material behind an import does not itself save
context. Relative import paths resolve from the importing file. These are
documentation observations, not a local measurement of the Claude runtime.

The [experimental alternative](../included/improved/skills/claude-md-generator-current/SKILL.md)
uses the active agent, actual project evidence and user-authorized scope. It
does not require a second model, fixed shell, universal line limit or fabricated
audit score. It is not a repair of the immutable mirror and has not been tested
for agent effectiveness. Its narrower review does not establish that the source
skill's other examples or bundled resources are correct.

The pinned source is `Varnan-Tech/opendirectory` commit
`bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4`. Its default branch was observed at
`caac7cda5621e289591e4e74b400e66ac72ad25b` on 3 November 2026, matching the
previous observation; this is not a full upstream update review. The skill's
README declares MIT, but a complete license file was not found at the source
repository, package, skills, or skill root in the pinned tree. This records a
source observation, not a legal conclusion. The mirrored `SKILL.md` does not
match its upstream Git blob after LF normalization, so the findings above refer
to the catalog mirror; they do not assert byte identity with upstream.

The [source observations](../artifacts/research/2026-11-03/claude-md-generator-review/source-evidence.json)
record source-API and document-capture hashes, individual resource identities,
and the failed current Google captures. Native API and browser captures remain
in the local research workspace.

The Claude documentation capture used the isolated Crawl4AI provider
`0.9.5+catalog.portable4`, returned HTTP 200 and has native SHA-256
`c0eae8908027defdf91292fd6931a6bd4fa069d5f9b7792dbda9491a65cfd874`.
The current Google changelog and deprecations URLs returned HTTP 301 and their
redirected captures did not contain the relevant model lifecycle text; neither
is used as a new retirement observation. Their native failure captures and the
GitHub API source observations remain in the local research workspace.
