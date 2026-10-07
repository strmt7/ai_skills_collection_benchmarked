# Karpathy upstream review

The collection's pinned general coding baseline is a third-party adaptation of
Karpathy's observations. GitHub redirects the historical repository name to
`multica-ai/andrej-karpathy-skills`. Its current default HEAD remains
`2c606141936f1eeef17fa3043a72095b4765b9c2`, matching the existing pin.
The standalone skill declares MIT in frontmatter. It is not a repository
maintained by Karpathy.

The public repository metadata listing for Karpathy's own GitHub account contains
63 repositories. That listing does not establish an absence of instruction files
inside them. Relevant primary sources were checked separately:

| Official source | Resolved default HEAD | Relevant observation |
|---|---|---|
| `karpathy/autoresearch` | `228791fb499afffb54b46200aca536f79142f117` | `program.md` separates editable training code from a fixed evaluator, begins with an unchanged baseline, limits each experiment and logs crashes/discards |
| `karpathy/nanochat` | `92d63d4e8bb4df75c3b71618f31ddde2378b2bcd` | Metadata `pushed_at` is newer than default-HEAD commit time; revision selection must resolve actual refs rather than treating activity timestamps as code updates |
| `karpathy/karpathy.github.io` | `717b06d57b7834e27ca4bd55bda0a79d16dddeca` | The 2026 post inventory includes `2026-02-12-microgpt.markdown`; no general replacement skill baseline was established by this inspection |

Primary links: [original research repository](https://github.com/karpathy/autoresearch),
[pinned experiment instructions](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md),
[official profile](https://github.com/karpathy),
and [pinned third-party skill](https://github.com/multica-ai/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/skills/karpathy-guidelines/SKILL.md).
The original X post could not be read through the browsing tool (HTTP 403);
its content was not independently reverified or quoted here.

Generalizable lessons for this collection are a fixed external evaluator,
an unchanged first baseline, bounded trials and an explicit failure ledger.
They do not justify importing the training-specific metric, a perpetual loop,
destructive branch resets, or an assumption that this host has the required GPU.
For coding-skill experiments, retain failed attempts as distinct statuses and
missing metrics as null, rather than ranking a crash's placeholder zero as a win.
