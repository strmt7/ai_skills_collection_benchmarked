# PPT Master SVG editor controls

These controls reproduce a text-move failure in the locked PPT Master v6.6.0
editor and check a separately prepared repair. The original browser raises an
undefined-function error before a keyboard nudge reaches the server. The repair
is checked against the real local backend for keyboard, drag and geometry edits,
including rejected requests and saved SVG output. Separate browser controls
exercise delayed responses after selection or slide changes.

The recorded run used Windows x64, Chromium 156.0.8078.4, Playwright 1.64.1
and Flask 3.1.3. It is a focused component check, not an agent benchmark or a
whole-presentation quality assessment. The latest upstream v6.7.3 source also
reproduced the missing function in an extracted-function fixture; this repair
is qualified only for the locked v6.6.0 distribution.

Prepare a repaired copy using the [repair entrypoint](../../../included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master/SKILL.md).
With Playwright and its Chromium installed in the Python running the controls,
and Flask installed in the separately specified backend Python, run:

```text
python benchmarks/component-controls/ppt-svg-editor/run_native.py --original-skill <locked-skill-directory> --repaired-skill <prepared-skill-directory> --backend-python <python-with-flask> --output <new-output-directory>
python benchmarks/component-controls/ppt-svg-editor/run_races.py --repaired-skill <prepared-skill-directory> --output <another-new-output-directory>
```

Each output parent must exist; outputs must be new directories outside both
skills. The first control starts owned loopback servers and saves fixtures only
under its output directory. Both controls block requests outside their test
origins and use a sandboxed headless browser. Inspect `result.json` and server
logs in the output directory. They do not change the locked mirror.
