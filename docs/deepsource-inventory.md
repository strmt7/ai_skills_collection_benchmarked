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

The collector makes no automatic retries and refuses redirects. If the provider
returns an HTTP error or blocks a request, preserve the response and follow the
provider's access instructions instead of changing clients to evade the refusal.
