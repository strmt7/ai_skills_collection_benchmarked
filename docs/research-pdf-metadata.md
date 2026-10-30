# PDF metadata example review

The [pinned PDF skill](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/pdf/SKILL.md)
reads `reader.metadata` and immediately accesses its attributes. A valid PDF
can have no document-information dictionary: in that case `metadata` is
`None`, and the example raises `AttributeError`. The
[pypdf API documentation](https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html#pypdf.PdfReader.metadata)
also notes that this property does not read metadata streams. Check for an
absent dictionary and inspect XMP separately when the task requires it.

On 30 October 2026, GitHub's contents API returned the same file blob,
`d3e046a5ae107a6cb23cfb16c219837094ab35d3`, for the pinned commit and
[upstream main commit `ca45fc4`](https://github.com/anthropics/skills/blob/ca45fc496a3436251f191354091d557da31c15b5/skills/pdf/SKILL.md).
Both returned file contents matched the blob and canonical SHA-256
`9f78b8359fbd4943ad260a7a1e436e5a96503406d6c34e99f69223d647d85b9c`.
This comparison covers the entrypoint file, not all adjacent resources.

The [component control](../artifacts/research/2026-10-30/pdf-metadata-controls/reproduce.py)
creates two synthetic PDFs: one without a document-information dictionary and
one with a title. On Windows with Python 3.13.17 and pypdf 6.21.4, the first
reproduced the exception and the second returned its title. The
[recorded result](../artifacts/research/2026-10-30/pdf-metadata-controls/result.json)
binds the observation to the canonical mirrored skill hash. A separate
[Linux control](../artifacts/research/2026-10-30/pdf-metadata-controls/linux-result.json)
with Python 3.12.3 and the same pypdf version produced the same outcomes.
Both environments passed `pip check`. Run the control in an isolated
environment with pypdf 6.21.4:

```text
python artifacts/research/2026-10-30/pdf-metadata-controls/reproduce.py
```

The exact mirrored snippet was also exercised against both cases independently.
The pypdf API page was captured on 30 October 2026 using Crawl4AI
`0.9.5+catalog.portable4` (HTTP 200; native result SHA-256
`b7d7377bef20d9f0c40097220c2f513d8d296de4dff27582ffac426e0ace1b30`).
This is a partial example review, not a full skill evaluation or an agent
benchmark. The source mirror is unchanged.
