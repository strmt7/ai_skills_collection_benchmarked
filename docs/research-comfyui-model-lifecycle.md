# ComfyUI model recommendation

The pinned [ComfyUI Workflow skill](../included/skills/by-category/devops-cloud-operations/creative-reference/twwch-comfyui-workflow-skill/SKILL.md)
recommends `claude-sonnet-4-20250514` for its Anthropic API loader. Anthropic's
[model lifecycle table](https://platform.claude.com/docs/en/about-claude/model-deprecations)
lists that model as retired. The skill also asks for the user's model
preference, so this is a stale recommendation rather than evidence that every
ComfyUI workflow fails. Check the provider's current model documentation and
the installed node's compatibility before selecting a replacement.

The [source-bound control](../artifacts/research/2026-10-30/comfyui-model-lifecycle/reproduce.py)
checks the skill's recommendation and model-choice instruction against the
captured Anthropic status. [Windows](../artifacts/research/2026-10-30/comfyui-model-lifecycle/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/comfyui-model-lifecycle/linux-result.json)
results match; an altered capture was rejected. It makes no model request and
does not test ComfyUI or score an agent. [Source evidence](../artifacts/research/2026-10-30/comfyui-model-lifecycle/source-evidence.json)
records the source and crawl identities; the native Anthropic capture remains
in the local research cache, and the control requires those exact bytes.

The source repository now resolves to `LingyiChen-AI/comfyui-workflow-skill`.
Its observed main commit matches the pinned commit. The source mirror is
unchanged, and this review does not qualify a replacement model or a complete
workflow.
