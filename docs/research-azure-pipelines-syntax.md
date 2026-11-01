# Azure Pipelines sequence preflight

The pinned Azure Pipelines validator's syntax component accepted four tested
bare scalar entries at the step, job and stage levels. Microsoft documents
[step](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps?view=azure-pipelines),
[job](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs?view=azure-pipelines)
and [stage](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/stages?view=azure-pipelines)
sequences. Template expansion also permits [step-list insertion](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-expressions?view=azure-devops),
so a scalar template expression cannot be treated as an ordinary bare literal.

The optional [sequence preflight](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/latest-release-devops/azure-pipelines-sequence-preflight/SKILL.md)
checks a narrow set of statically visible literal shapes and reports unresolved
template forms separately. It is not Azure schema validation: for instance, it
does not check task versions, although the original component caught a missing
version in the control. A zero exit status is not a pipeline validity claim.
Validate and run the result in the intended Azure service.

Nine independent local YAML controls were run against the pinned original and
the preflight on Windows and Linux. The original accepted all four bare
entries, while the preflight reported them; both accepted the ordinary case,
and the preflight marked the two template cases indeterminate. An explicit
CP1252 stdout control caused the original to raise `UnicodeEncodeError`; the
preflight produced ASCII JSON. Ordinary controls used UTF-8 mode. These results
do not establish how every Windows environment is configured. Raw streams are
retained outside the repository; [result digests and reproduction](../artifacts/repaired-skill-readiness/azure-pipeline-sequence-preflight-v1/qualification.json)
are source-bound here. No Azure service or coding-agent benchmark was run.

The pinned and observed upstream versions have identical `SKILL.md` and syntax
component blobs, but other files in that upstream skill changed. The original
mirror remains unchanged, and its other components were not assessed here.
