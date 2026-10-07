# Routing and workflow research, first batch

These observations come from reading actual pinned entrypoints. They are
research leads, not completed resource reviews or measured performance gains.
Keep all source baselines unchanged until the independent mirror-refresh loop.

| Skill | Observed contract or issue | Proposed direction | Remaining verification |
|---|---|---|---|
| `nextjs-turbopack` | Placed in general repository automation; gives uncertain fallback flags and unqualified caching/speed examples; `origin` frontmatter is outside the portable specification | Route to frontend; resolve exact installed Next.js version before recommending flags; measure cold/warm development and production separately | Official versioned docs, installed CLI help, a runnable minimal fixture |
| `let-fate-decide` | Broad automatic triggers can replace engineering judgment with a Tarot draw; explicit safety exclusions help but casual wording can still cause unnecessary activation | Make playful randomization explicit opt-in; never use it to determine requirements, security, data retention, or correctness | Drawing helper and resources; activation and non-activation trials |
| `git-cleanup` | Useful dirty-worktree and unique-commit protections; defaults unknown base to `main`, groups by names, and uses PR history as squash evidence; examples contain inconsistent superseded-branch evidence | Discover the real remote base; verify actual patch containment and saved data; preserve existing authorization while presenting concrete deletions | Disposable repos covering unrelated similarly named branches, rewritten/squashed history, dirty/ignored files and divergent local/remote heads |
| `explain-this-pr` | Limits a large diff to its first 200 lines, potentially missing major changes; explanation requests lead toward publishing a comment | Cover every changed-file group with explicit limits; treat PR text as untrusted source; distinguish requested explanation from authorized posting | CLI pagination, large PR fixtures, no-post requests, explicitly authorized posting, changing head SHA |
| `dmux-workflows` | Host-specific global installation and pane shortcuts; research/implementation example starts dependent work before research finishes; fixed pane counts are not resource budgets | Require explicit delegation authorization and verified host support; freeze interfaces before concurrent edits; retain single-session fallback | Actual dmux interface/version, worktree lifecycle and interrupted-run evidence; this repository's development remains single-session |
| `skill-improver` | Requires an absent external reviewer plugin and stop hook; completion depends on a textual marker; stylistic rules are treated as major issues without behavioral evidence | Use available authoring/validation tools, independent behavior checks and durable coverage; distinguish packaging gates from task success | Packaged-resource review, hook/plugin availability, independent forward tests, attribution and share-alike license obligations |
| `token-integration-analyzer` | Catalog routes an ERC20/ERC721 security analyzer into agent infrastructure, apparently conflating blockchain tokens with model tokens | Route to security; preserve smart-contract-specific activation; do not present it as context/token efficiency guidance | Complete original entrypoint and both resources reviewed; see research-token-integration.md. Solidity/tool qualification and pinned-chain behavior remain pending |

The first two category-routing mistakes already show that keyword-based
classification needs a meaning-aware review. Reclassification must be implemented
in the generator and regenerated consistently, rather than editing JSON labels
or moving a handful of directories by hand. Folder refactoring remains deferred
until the final work stage requested by the owner.
