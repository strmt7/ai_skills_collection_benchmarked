# Current dependency controls for the pinned image CLI

The package declaration and complete npm lock resolve the nine direct packages
to stable versions observed from the primary npm registry on 2 October 2026.
This is an experimental control graph, not a silent replacement of the source
mirror. The ISC notice retains the original package's copyright.

Provision the complete pinned mirror into a new workspace directory:

```bash
python tools/prepare_image_cli_controls.py --stage .venv/image-cli-controls --json
npm ci --ignore-scripts --prefix .venv/image-cli-controls
npm audit --prefix .venv/image-cli-controls
node benchmarks/dependency-regressions/image_cli_current_controls.mjs \
  --package-root .venv/image-cli-controls --output image-cli-controls.json
python tools/prepare_image_cli_controls.py --stage .venv/image-cli-controls --check
```

Use the qualified current Node/npm runtimes; the observed run used Node 26.10.0
and npm 12.2.0. Installation fetches registry packages; runtime controls intercept
all provider/asset fetches with local responses. Child CLI configuration and
output are confined to a unique temporary fixture. Existing stages/results are
never overwritten. Inspect retained temporary control files before removing them.

The driver checks image conversion, fallback accounting, current Google SDK
response parsing and CLI imports. It also reproduces two negative contracts:
short-key masking crashes and failed QA still reports success. Passing these
negative controls means the defects were reproduced, not that the behavior is
correct. No provider model availability, image aesthetics or agent efficacy is
established. The live npm advisory receipt reports known advisories at that run;
zero findings does not certify absence of vulnerabilities.
