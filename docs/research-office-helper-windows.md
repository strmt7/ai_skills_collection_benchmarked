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
