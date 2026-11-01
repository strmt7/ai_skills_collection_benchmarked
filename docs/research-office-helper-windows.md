# LibreOffice helper on Windows

The pinned Anthropic and scientific DOCX, PPTX and XLSX skills each bundle the
same LibreOffice helper. The DOCX and PPTX instructions use it for conversion;
the XLSX recalculation script imports it. On the tested Windows host, the
helper fails before starting LibreOffice because the Python `socket` module
does not expose `AF_UNIX` in the tested runtimes. Workflows that use other
tools or do not invoke this helper were not assessed by this control.

The [reproducer](../artifacts/research/2026-10-30/office-helper-windows/reproduce.py)
verifies the exact SHA-256 of all six helper copies, then invokes each helper
with `--version` in a separate Python subprocess. The results for
[Python 3.11.9](../artifacts/research/2026-10-30/office-helper-windows/windows-3.11.json),
[3.12.10](../artifacts/research/2026-10-30/office-helper-windows/windows-3.12.json),
[3.13.17](../artifacts/research/2026-10-30/office-helper-windows/windows-3.13.json),
and [3.14.8](../artifacts/research/2026-10-30/office-helper-windows/windows-3.14.json)
record 24 startup failures. LibreOffice was available on the process path,
but none of these controls launched it. The subprocesses used a disposable
profile directory that remained empty. An altered helper was rejected by the
source check. The result paths in captured error text replace the repository
root with `<repository>`; the remaining error text is retained.

Run the control on an affected Windows Python installation from the
repository root:

```text
python artifacts/research/2026-10-30/office-helper-windows/reproduce.py --root .
```

The control does not test actual document conversion, presentation rendering,
spreadsheet recalculation or agent performance. The separate
[spreadsheet review](research-xlsx-recalculation.md) records additional
recalculation and newer-upstream controls; the
[DOCX portability review](research-docx-portability.md) covers a separate
npm installation issue. The pinned source mirrors remain unchanged.

## Comparison with newer DOCX upstream

The [newer DOCX entrypoint](https://github.com/anthropics/skills/blob/ca45fc496a3436251f191354091d557da31c15b5/skills/docx/SKILL.md)
tries `require('docx')` first and recommends a local `npm install docx` if the
import fails. That differs from the pinned global-install guidance discussed in
the [DOCX portability review](research-docx-portability.md). The newer
entrypoint assumes the package is preinstalled, and this comparison did not run
its complete document workflow. Its source SHA-256 is
`8017469ea95fb7d28225c62daf8e2f3492a7b516fc64c18c28977cbf8980b7fe`.

The newer commit also changes the helper to create a temporary LibreOffice
profile. A [separate source-bound control](../artifacts/research/2026-11-01/docx-upstream-helper/reproduce.py)
compared the exact upstream [old helper](https://raw.githubusercontent.com/anthropics/skills/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/docx/scripts/office/soffice.py)
and [new helper](https://raw.githubusercontent.com/anthropics/skills/ca45fc496a3436251f191354091d557da31c15b5/skills/docx/scripts/office/soffice.py).
On Windows Python [3.11.18](../artifacts/research/2026-11-01/docx-upstream-helper/windows-3.11.json),
[3.12.16](../artifacts/research/2026-11-01/docx-upstream-helper/windows-3.12.json),
[3.13.18](../artifacts/research/2026-11-01/docx-upstream-helper/windows-3.13.json)
and [3.14.10](../artifacts/research/2026-11-01/docx-upstream-helper/windows-3.14.json),
both failed before starting LibreOffice with `socket.AF_UNIX` unavailable. The
child process used an empty PATH and disposable profile and temporary directories.
No document conversion or agent evaluation was performed; this does not establish
behavior on other Windows builds or systems where `socket.AF_UNIX` exists.

To reproduce, save the two linked raw files without newline conversion and run
the control on a Windows Python without `socket.AF_UNIX`:

```text
python artifacts/research/2026-11-01/docx-upstream-helper/reproduce.py --old <old-helper.py> --new <new-helper.py>
```

The control verifies both Git blob IDs and SHA-256 digests before execution and
checks the files again afterward. The upstream snapshot is not a mirror update;
its other changes remain unqualified.
