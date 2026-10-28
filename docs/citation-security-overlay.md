# Citation management: URL-classification repair

The [citation-management security overlay](../included/repaired/skills/citation-management-security/SKILL.md)
is an opt-in version of the locked citation skill. It checks the actual URL
hostname when identifying DOI, PubMed and arXiv links. For example, a hostname
that merely contains `doi.org` is no longer treated as the DOI service.

Use the overlay within this checkout so that its linked agent-tool policy and
supporting files are available. The overlay retains the original skill text and
the upstream MIT license in its `provenance/` directory. Its
[`repair.json`](../included/repaired/skills/citation-management-security/repair.json)
records its source, changes and file hashes. Check the overlay with:

```sh
python tools/check_citation_security_overlay.py --check --json
```

The [security control](../artifacts/research/2026-10-28/citation-url-security-control.json)
records the observed failure in the locked skill and comparison with a newer
upstream version. The repair is tested with independent URL cases. These checks
do not establish complete skill security or improved agent performance. The
original mirror is unchanged and its code-scanning alerts remain open.
