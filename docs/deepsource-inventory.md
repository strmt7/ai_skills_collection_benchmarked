# DeepSource inventory

Use the official [DeepSource GraphQL API](https://docs.deepsource.com/docs/product/api-and-webhooks)
to inspect the full default-branch occurrence inventory. DeepSource's GitHub App
can run analysis without a GitHub Actions secret; a GraphQL request requires an
authenticated DeepSource personal access token. The collector reads an existing
official CLI login or `DEEPSOURCE_TOKEN` from the environment. It never accepts
a token as a command-line argument.

After the requested commit's DeepSource analysis finishes, create a new output
directory under `.venv` or outside the checkout:

```text
python -c "from pathlib import Path; Path('.venv').mkdir(exist_ok=True)"
python tools/deepsource_inventory.py --repository OWNER/REPOSITORY --commit COMMIT_SHA --output .venv/deepsource-inventory
```

Replace the repository and commit placeholders with the GitHub repository and
full default-branch commit SHA. Use `--branch` if the default branch is not
`main`. The output directory must not already exist. It contains native response
pages, a final consistency observation, newline-delimited findings and a
manifest. Provider responses can contain sensitive information; keep the output
private and review it before sharing. Do not commit it to the repository.

The collector verifies the repository, branch, completed analysis and commit on
each page, checks unique occurrence IDs and the provider's total count, then
rechecks the first occurrence and count. Once capture starts, failures retain an
incomplete manifest and partial evidence when local I/O permits. Treat findings
as complete only when the manifest says `complete: true` and their hash matches.
DeepSource does not guarantee snapshot isolation, so these checks cannot prove
that every concurrent change was detected. A complete inventory is not a clean
bill of health: each finding still needs review and remediation.

## Remediation workflow

Use the complete DeepSource inventory together with all pages of open GitHub
code-scanning alerts for the same default-branch commit. Keep the original
responses, scan configuration, analyzer versions and commit identity with the
comparison; counts from different commits or coverage are not interchangeable.

Group occurrences by ownership, source repository, rule and shared root cause.
Prioritize exposed security and secret findings, then correctness and the
remaining quality findings. Review representative instances and any differing
data flows before applying a shared fix; a rule name alone does not establish
that every occurrence has the same cause. Test fixes against affected behavior,
including negative controls, and retain the results.

Repository-owned tools and tests can be corrected directly. Generated artifacts
must be corrected through their source and regenerated. Mirrored skills remain
source-locked: use a verified upstream correction and regenerate the mirror, or
record an explicit repaired overlay and its provenance. An overlay does not
resolve a finding still present in the original mirror. If no upstream correction
is available, retain the finding and its impact as open work.

After each batch, rerun relevant local checks and wait for hosted analysis on
the published commit. Capture a fresh complete inventory, compare findings by
stable identity and root-cause group, and investigate newly introduced findings
and unexplained disappearances. Do not disable analyzers, exclude paths,
suppress findings or change thresholds to make the counts appear lower.

The collector applies socket and response-read limits, makes no automatic retries
and refuses redirects. If the provider
returns an HTTP error or blocks a request, preserve the response and follow the
provider's access instructions instead of changing clients to evade the refusal.
