---
name: repository-conventions-current
description: Check imported or generated repository convention profiles against the current project before applying them. Use during repository onboarding or when copied guidance conflicts with current instructions, manifests, tooling or CI.
license: MIT
---

# Verify repository conventions

Apply the repository's [mandatory agent tools](../../../../docs/agent-tools.md)
and controlling instructions before relevant work. This experimental adaptation
preserves its original project-specific profile in `provenance/`. It does not
turn that historical profile into a policy for every repository. Agent efficacy
is unbenchmarked.

Bind a profile to its actual source project, revision and relevant evidence.
An imported document saying “this repository” still refers to its original
project until the current repository establishes otherwise. Distinguish an
upstream rename from deletion; follow recorded path history and preserve the
original identity and evidence.

Read the controlling instructions, applicable manifests, formatter/type settings,
test entrypoints and CI for the part being changed. Confirm a few relevant live
examples. Resolve contradictions by authority and current evidence, not by a
commit-message pattern or a generic coding preference.

- Do not infer migration frequency, architecture or test coverage from example
  commit titles. A historical claim needs its dataset and method before it can
  justify a policy or measured statistic.
- Honor the required author/committer identity, branch and publication rules.
  Never copy a previous identity or change global configuration to match an
  imported profile. A commit style is distinct from a commit identity.
- Use the project's actual language, test discovery and quality gates. A foreign
  `*.test.js` convention or 80% coverage target does not replace local contracts.
  Add tests that exercise the changed risk, rather than padding a percentage.
- Preserve the supported OS, execution environment and harness. Discover paths
  and installation inputs explicitly; host independence does not authorize an OS
  port, global hook installation or a new framework.
- Keep useful original failures. Without recovery or useful added context,
  allow the operation's failure to propagate. Inside the existing async caller:

```typescript
return await operation();
```

When adding context is justified, preserve the cause and cancellation semantics.
Record what was actually checked and which imported claims remain unsupported.
Keep onboarding evidence short enough to stay useful on subsequent changes.
