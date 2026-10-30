# Gemini image model lifecycle

The pinned [Gemini Image Generation skill](../included/skills/by-category/devops-cloud-operations/creative-reference/gemini-image-generation/SKILL.md)
shows `gemini-3.1-flash-image-preview` as an example `GEMINI_MODEL_ID` for the
Google GenAI SDK. Google's [deprecation page](https://ai.google.dev/gemini-api/docs/deprecations)
marks that model as already shut down. Its table lists June 25, 2026; Google
explains that table dates are earliest possible retirement dates. The skill
accepts a user-selected model ID, so this finding concerns the example rather
than every possible configuration.

The separate [Generate Image skill](../included/skills/by-category/science-research-data-analysis/latest-release-community/generate-image/SKILL.md)
uses `google/gemini-3.1-flash-image-preview` as its OpenRouter default. On
October 30, 2026, the [OpenRouter model catalog API](https://openrouter.ai/api/v1/models)
still listed that provider-specific ID. A catalog entry does not prove a live
request will succeed, and Google's direct API status does not by itself establish
the OpenRouter route's status. No image-generation request was made.

At the inspected [current upstream scientific skill](https://github.com/K-Dense-AI/scientific-agent-skills/blob/5f2bc0341354fd5590aef76a533ada1e1e5b4e62/skills/generate-image/scripts/generate_image.py),
the script's default is `google/gemini-3.1-flash-image`; that ID was also listed
in the captured OpenRouter catalog. The current Google-skill source commit
matches its pinned commit. These source checks do not qualify a full upgrade or
show that either model works with the complete skill.

The [source-bound control](../artifacts/research/2026-10-30/gemini-image-lifecycle/reproduce.py)
checks the Google page's shutdown legend and model row, the OpenRouter catalog,
the pinned examples and defaults, and the inspected upstream default. Its
[Windows](../artifacts/research/2026-10-30/gemini-image-lifecycle/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/gemini-image-lifecycle/linux-result.json)
outputs match; an altered capture was rejected. The exact source identities and
capture digests are in [source evidence](../artifacts/research/2026-10-30/gemini-image-lifecycle/source-evidence.json).
The native Google and OpenRouter captures remain in the local research cache;
the control requires those exact captured bytes and the inspected upstream
script, not a newly downloaded response. No agent performance was measured.
