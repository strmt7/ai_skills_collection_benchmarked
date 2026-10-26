# Frontend and browser skill review

The three skills in the frontend/UI/browser category contain five resources.
All five instruction/metadata bodies were read. The locked mirrors remain
unchanged. Two separate MIT-licensed experimental overlays now address the
TypeScript and React request contracts below, preserving original text and UI
metadata in provenance. Their agent-performance status remains **unbenchmarked**.
Broader framework, browser and agent qualification remains open in the ledger.

## Source review and upstream comparison

| Skill | Resources reviewed | Result |
| --- | --- | --- |
| ECC coding standards | `SKILL.md`, `agents/openai.yaml` | Shared-input mutation, failure provenance, Zod 4 compatibility and overbroad rules reviewed; scoped overlay added. |
| ECC frontend patterns | `SKILL.md`, `agents/openai.yaml` | Effect identity, stale results, disabled state, cleanup and partial accessibility examples reviewed; scoped overlay added. |
| Trail of Bits Chrome troubleshooting | `SKILL.md` | Platform-specific recovery assumptions reviewed; no commands executed and no OS port or replacement published. |

ECC's locked commit is `846ffb75da9a5f4e677d927af1ad4a1951652267`.
The inspected upstream main is `f3904009440af24f00617343910ee89714df8be3`.
The selected upstream texts fix shared-array sorting and stabilize the query
callback across inline fetcher/options identities. They also clarify activation
scope. The source still uses the removed Zod `.errors` accessor, discards the
original fetch error, and lacks request-generation cleanup in the query example.
The full source cohort has not been refreshed: two selected-file comparisons
cannot qualify every skill in that repository. Exact source captures, Git blob
verification and primary-source crawl digests are recorded in
[`frontend-review.json`](../artifacts/research/frontend-contracts/frontend-review.json).

The authored [coding overlay](../included/improved/skills/coding-standards-current/SKILL.md)
and [frontend overlay](../included/improved/skills/frontend-patterns-current/SKILL.md)
replace blanket rules with explicit ownership, validation, failure and lifecycle
contracts. They retain normal prose and progressive references. They do not
install global agent configuration, change frameworks or imply an OS migration.
The frontend reference deliberately omits the original callback-hook API, cache
and SSR; its narrower contract is documented rather than silently presented as
an API-compatible replacement.

## Executable evidence

The [component-control method](../benchmarks/component-controls/frontend/README.md)
records eight independently stated API/application contracts. Locked excerpts
meet 1/8, the inspected upstream excerpts meet 3/8, and maintained examples meet
8/8. Both source arms produce the same Zod 4 type error. All misses and native
compiler output are retained. Tests use actual React 19.3.1, Zod 4.6.7,
TypeScript 7.0.2 and jsdom 30.1.3, with Node 26.12.1 and npm 12.2.1. Exact direct
versions and the transitive lock are retained; install scripts were disabled.

The test author had seen the skill text. These are targeted regression controls,
not a blind skill comparison, a representative task sample or proof of agent
efficacy. The declared contract treats a newer key/refresh as superseding an old
request and clears state when disabled; other products may deliberately choose
different cache semantics. Whole examples containing placeholder implementations
were not compiled as complete applications, and their omitted context is not
counted as a failure.

The oracle contract was frozen before the authored candidate examples. A bounded
request-loop guard in the controller was corrected before candidate execution;
no expected result changed. After the first native comparison, the maintained
example's unnecessary explicit Zod issue type was removed. The final comparison
reran all arms, and targeted lifecycle tests separately exercised StrictMode,
ignored cancellation, real abort signals, disable, unmount and non-Error failures.
This does not test a real browser, accessible focus behavior, framework routing,
server rendering, query caching or an AI agent's task success.

## macOS troubleshooting boundary

The Trail of Bits source is explicitly macOS-only. Its pinned commit is
`e8cc5baf9329ccb491bfa200e82eacbac83b1ead`; the inspected main is
`196a9073ab10d35bacf111f945e02c00b2c6883a`. Fetching the old skill path at that
head returns HTTP 404, and a complete recursive tree contains no matching skill
basename. That establishes a missing path, not the absence of a successor or an
explanation for removal. The pinned root license is CC-BY-SA-4.0, not ECC's MIT.

The source includes broad process termination, socket removal, wrapper selection
by modification time, shell edits and disabling another integration. None was
executed. Such recovery requires current, version-specific ownership evidence;
a machine-specific workaround must not become a default install instruction.
The Chrome protocol supports separately named native hosts, so it does not by
itself support a universal claim that two integrations cannot coexist.

Current vendor guidance starts with `/chrome` status/reconnect and distinguishes
extension, authentication and organization state. It is evidence for reviewing
the old instructions, not proof that this legacy macOS setup works. Native macOS
qualification and any successor-path investigation remain open. There is no
Windows adaptation of this skill; host independence does not authorize one.

## Primary sources

These page bodies were extracted using the reviewed isolated Windows Crawl4AI
provider `0.9.5+catalog.portable4`, with robots/TLS/sandbox checks, disclosed
automation, no personal profile, no stealth, no external LLM and no retry/fallback.
Native status, errors, output digests and reviewed sections are retained in the
research record; full browser captures stay in ignored local evidence.

- [React Effect cleanup and data-fetch races](https://react.dev/reference/react/useEffect#fetching-data-with-effects).
- [React purity and StrictMode memo calculations](https://react.dev/reference/react/useMemo#my-calculation-runs-twice-on-every-re-render).
- [Zod 4 migration and removed error APIs](https://zod.dev/v4/changelog).
- [Response success status](https://developer.mozilla.org/en-US/docs/Web/API/Response/ok).
- [Preserving an error cause](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/cause).
- [Chrome native messaging and host selection](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging).
- [Claude Code Chrome setup and reconnect guidance](https://code.claude.com/docs/en/chrome).
