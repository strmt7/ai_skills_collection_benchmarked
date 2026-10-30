# DOCX skill portability review

This is a partial review of the pinned Anthropic DOCX skill, not an agent
benchmark or a review of every document workflow. The catalog mirror remains
unchanged at source commit `2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c`;
its entrypoint has SHA-256
`cfbabd72b1aec7dfaad988fb6e5e16b27dc744b9a00cae15db9045e95f53903e`.

## Installation finding

The skill recommends `npm install -g docx` and then imports the package with
`require("docx")`. npm's [folder documentation](https://docs.npmjs.com/cli/v11/configuring-npm/folders/)
recommends installing a dependency locally when requiring it. On Windows x64
with Node.js 24.22.1, npm 11.19.1 and `docx` 9.15.0, an isolated global-prefix
installation loaded by its explicit path but `require("docx")` from a separate
consumer failed with `MODULE_NOT_FOUND` when `NODE_PATH` was unset. Installing
the same package locally in that consumer made the import succeed. This is one
configuration; other module paths can change the outcome.

For a self-contained document project, declare and install the dependency in
that project's local package environment, then verify the import before running
the document-generation code. Choose and qualify a version for that project;
a global installation alone is not a portable module-resolution contract.
The source skill also uses `fs.writeFileSync` in its setup example without
showing an `fs` import in that snippet, so a standalone script needs one.

## Page-size controls

The same package version produced A4 portrait by default, explicit US Letter
portrait, and Letter landscape when supplied the skill's portrait dimensions
and landscape orientation. The observations inspect `word/document.xml`
page-size attributes, not a rendered or printed document. The
[9.15.0 section-properties source](https://github.com/dolanmiu/docx/blob/9.15.0/src/file/document/body/section-properties/section-properties.ts)
provides the corresponding version-specific implementation context.

The [control script](../artifacts/research/2026-10-30/docx-controls/reproduce.py)
uses a fresh temporary directory, private npm cache and separate global-prefix
and local installations; it leaves the caller's global npm packages unchanged.
Run it with Python, Node.js, npm and network access:

```text
python artifacts/research/2026-10-30/docx-controls/reproduce.py
```

The [recorded output](../artifacts/research/2026-10-30/docx-controls/result.json)
is the Windows run described above. The experiment pins the top-level `docx`
version, not the entire transitive dependency graph. It does not test
LibreOffice, Word, Google Docs, fonts, rendering, tracked changes, accessibility,
or other versions and operating systems.

## Source capture and remaining work

The npm documentation and versioned `docx` source were read with the isolated
Crawl4AI provider `0.9.5+catalog.portable4` on 30 October 2026. Both returned
HTTP 200 with substantive relevant content; native-result SHA-256 digests are
`c6f3c4d2f5fab8ebd85ac604825cb1e29cc6cc16c5baa5cca11c82c39d26ee24` and
`554f79455e8787483cbb4ab3fdcde863cfd262bfdbf246cd8ef6fbc99fe233ee`,
respectively. The native captures remain local research evidence. A search
result for an older API documentation URL returned HTTP 404 and was rejected.

The installation concern warrants an independently evaluated repair or
upstream correction. These controls do not establish that an agent used this
skill successfully, that its other instructions work, or that it improves an
agent over a baseline.
