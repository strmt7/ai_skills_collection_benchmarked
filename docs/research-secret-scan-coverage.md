# Secret detection coverage and declared neutralization

The previous curated scanner did not include Stripe secret/restricted keys or
webhook signing secrets. It also omitted untracked publishable files, root-commit
contents, history outside HEAD and merge-only changes. Its previous zero-finding
result did not establish absence of these classes. The existing unfiltered
Gitleaks source-context review remains separate and unresolved.

The scanner now includes tracked and non-ignored untracked worktree files with
NUL-separated names; it reads commits reachable from all local refs and includes
root/first-parent merge differences. New patterns cover Stripe server secret,
restricted, organization and webhook shapes, including provider-shaped teaching
values. Public/publishable keys and neutral placeholders are distinguished by
their documented credential semantics. No allowlist, finding dismissal or path
exemption was added. Git object content is read through one NUL-framed process,
one blob at a time, preserving newline filenames. Incomplete protocols return an
explicit infrastructure failure, not a clean verdict. A union prefilter retains
multiple/overlapping rule findings while avoiding a Python rule loop on most
ordinary lines. Existing binary/non-text and ignored-file scope is unchanged.

Owned temporary Git controls qualify root, separate-ref, merge-only and newline
filename cases. Pattern controls qualify overlapping findings, sensitive key
families and non-secret placeholders. Header bounds/EOF and CLI infrastructure
failures are exercised. Temporary commits use command-scoped `AI agent <>`
identities; the collection's actual repository history was not altered.

The actual expanded worktree scan exposes eleven Stripe-shaped examples. The
all-local-ref history scan exposes twenty-two occurrences. Findings contain
locations/rules only, never matched credential text. These are not proof that a
token authenticates; no live credential validation or provider request was made.
The clean-tree test now correctly fails and its expectation remains unchanged.
The historical Git rename-limit warning affects rename classification rather
than suppressing added-file content; it is retained in the raw observation.

Source generation offers explicit `--credential-policy 2`, recording
`credential_policy_version` in generated catalog, mirror manifest and
source-lock records. Version 1 remains the default for exact existing-lock replay.
Version 2 shares the scanner's two Stripe patterns and replaces credential shapes
with neutral server/webhook markers. It also neutralizes entrypoint metadata
before rendering it into generated summaries. Unknown policies fail closed,
including binary inputs. Fixture tests verify raw source preservation, idempotent
copying, matching portable hashes, complete publication/freshness and declared
policy consistency through mirror and live-source validation.

The subsequent local publication regenerated seven affected skill trees from
four clean public checkouts at their original locked commit/tree SHAs. Every raw
source tree first reproduced its previous canonical mirror hash. Version 2 then
neutralized eleven examples across eight resources. Semantic catalog metadata,
source URLs, commits and unrelated mirror content were preserved. Catalog,
mirror/selected manifests and source-lock hashes were updated together through
the qualified recoverable publisher. The exact changes, portable Git modes and
original/updated hashes are recorded in `credential-policy-refresh.json`; the
originals and publication journal remain in ignored recovery storage.

`tools/refresh_credential_policy.py` makes this limited source loop reproducible:

```sh
python tools/refresh_credential_policy.py --source-root PATH_TO_PINNED_CHECKOUTS \
  --receipt artifacts/research/NEW_RECEIPT.json --check --json
```

Remove `--check` to publish the reviewed refresh. The receipt must be new; source
origin, commit, tree, cleanliness and old-policy equivalence are checked before
copying. Unverified inputs and metadata changes requiring full regeneration are
rejected. This is a credential transformation, not an upstream version upgrade.
Sixteen focused migration/serialization controls pass, including wrong origins/
commits, changed source/mirror inputs, retained originals, repeated freshness
and preservation of metadata field order and Unicode escaping.

Live validation checks all seven refreshed skills against those four original
checkouts; this does not establish live verification of every other source.
All 673 mirror/catalog and offline source-lock checks pass. The expanded curated
worktree scan now returns zero findings. The later full suite reports 547 passes
and two documented platform skips, with 69.36% coverage; its clean-tree assertion
was preserved. Static benchmark, risk-audit and badge freshness checks pass.

Repository history was not rewritten. Its twenty-two previously observed
occurrences and the separate unfiltered Gitleaks findings still require
remediation. Fresh branch/PR identity audits and hosted scanner/alert results
remain required before delivery. A passing curated worktree check is not an
overall security-clean result; no finding was suppressed or dismissed.

The broader post-refresh Gitleaks observation stages all 7,868 tracked and
non-ignored untracked publishable files. Its 119 findings include 68 prior
locations and 51 additional locations in evidence files; five prior locations
no longer appear. These counts have different file denominators and do not
establish an overall decrease. The additional contexts were inspected: owned
container correlation labels, file SHA-256 provenance and nontext resource
inventory reasons. The observations and contextual classification are recorded
separately. Legitimate evidence was retained, and all scanner findings remain
visible. The source findings still need remediation. The initial adapter's
incorrect assumption that the whole Gitleaks Match field is redacted was fixed;
the successful replay verifies Secret redaction and publishes locations only.

Primary credential semantics:
[Stripe API key types](https://docs.stripe.com/keys),
[webhook signing secrets](https://docs.stripe.com/webhooks/signature).
These detection controls are unrelated to coding-agent benchmark scores.
