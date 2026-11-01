# Install and use a skill

You can [browse the catalog](catalog/index.md) without installing the Python
tooling. Each entry links to its locked source, bundled resources and recorded
evidence. Catalog inclusion does not establish compatibility with your agent or
successful execution in your environment.

## Get a local copy

Clone the collection into a directory you choose:

```powershell
git clone https://github.com/strmt7/ai_skills_collection_benchmarked.git
cd ai_skills_collection_benchmarked
```

Keep the repository structure intact. Agent-ready entrypoints and maintained
overlays contain relative links to resources, provenance and the agent-tool
policy. Copying a `SKILL.md` file alone can break those links.

## Choose a skill

1. Find your task in the [catalog](catalog/index.md) or
   [selected skills](selected-skills.md).
2. Read the skill's requirements, licence and evidence. Check the required
   operating system, runtime, external service and data access.
3. Choose the locked [source mirror](../included/skills/README.md) for the
   original instructions, or an explicitly documented repaired/maintained
   overlay when its tested scope fits your task. The original mirror remains
   available for comparison.

Some reviewed instructions have known limitations:

- The pinned AnnData skill incorrectly says backed-mode metadata changes are
  saved automatically. [Review the tested I/O findings](research-anndata-10x.md)
  before using it with data you need to preserve.
- With GNU Make 4.4.1, the pinned Makefile generator's selective `.NOTPARALLEL`
  example does not serialize the named target recipes. [See the parallelism control](research-makefile-parallelism.md).
- The pinned DOCX skill's global npm installation does not necessarily make the
  library importable by a local script. [See the portability control](research-docx-portability.md).
- The bundled LibreOffice helper in the DOCX, PPTX and XLSX skills fails to
  start on the tested Windows Python runtimes. [See the shared-helper control](research-office-helper-windows.md).
- The pinned PDF skill's metadata example fails without an information
  dictionary, and its image example does not always produce JPEGs. [See the tested cases](research-pdf-metadata.md).
- Several text examples in the pinned theme showcase have low contrast.
  [Review the measured colors](research-theme-contrast.md) before applying a theme.
- The pinned infographic exporter can report success without producing an SVG
  when its converter is missing. [See the export control](research-infographic-export.md).

- The pinned XLSX helpers can misreport simulated timeouts and literal error
  text. [See the recalculation controls](research-xlsx-recalculation.md).
- The pinned docs-from-code fallbacks can miss or misidentify routes, and the
  TypeScript fallback failed to start in the tested environment. [See the extractor controls](research-docs-from-code.md).
- Eight skills hardcode a retired Gemini model; one more names it while allowing
  an alternative. [See the model review](research-retired-gemini-model.md).
- One Google image-skill example names a shut-down preview model; the related
  OpenRouter ID is a separate provider entry. [See the image-model review](research-gemini-image-lifecycle.md).
- The ComfyUI skill recommends a retired Anthropic model while allowing a
  different model choice. [See the model review](research-comfyui-model-lifecycle.md).
- The design skill's local searches and HTML renderer can report success when
  required input is missing. A [local-search repair](../included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design/SKILL.md)
  is available; the brief generator and renderer remain unchanged. [See the tested cases](research-design-search.md).
- The testing-workflow skill's Jest threshold example uses an unrecognized
  option. A [testing-workflow repair](../included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/tdd-workflow-everything-claude-code/SKILL.md)
  corrects it. [See the tested cases](research-tdd-jest-configuration.md).

- The E2E skill can register its response wait too late. An [E2E repair](../included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/e2e-testing/SKILL.md)
  addresses the ordering. [See the timing controls](research-e2e-response-order.md).

- The Bun skill assumes frozen installs are always locked. A [Bun repair](../included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/bun-runtime/SKILL.md)
  makes the lockfile precondition explicit. [See the runtime controls](research-bun-runtime.md).

- The Playwright skill executor replaces the caller’s module search path. A
  [maintained executor](../included/repaired/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill/SKILL.md)
  preserves it. [See the tested cases](research-playwright-executor.md).

- The Makefile generator can lose required PIC flags and ignore shared-link
  settings. A [C generator repair](../included/repaired/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-generator-c/SKILL.md)
  covers C executables and Linux ELF libraries. [See the build controls](research-makefile-generator-c.md).

- The Next.js skill contains outdated bundler and analysis guidance. A
  [version-specific repair](../included/repaired/skills/by-category/coding-refactoring-repository-automation/selected-structure-reference/nextjs-turbopack/SKILL.md)
  records the tested commands. [See the component controls](research-next-turbopack.md).

- The Anthropic API skill contains an older model table and default. [Review the
  current-source comparison](research-anthropic-api.md) before selecting a model.

- A [source comparison](research-anthropic-upstream.md) records upstream changes
  for all 17 pinned Anthropic skills; it does not qualify the changed files.

- The pinned Azure Pipelines basic example assumes a specific npm test flag and allows lint failure. A [Node CI overlay](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/latest-release-devops/azure-pipelines-node-ci/SKILL.md) covers a tested native-test-runner case. [See the review and limits](research-azure-pipelines-node.md).

- The pinned Azure Pipelines syntax component accepts tested bare sequence entries. A [limited sequence preflight](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/latest-release-devops/azure-pipelines-sequence-preflight/SKILL.md) identifies those shapes without claiming Azure schema validation. [See the controls and limits](research-azure-pipelines-syntax.md).

- The pinned Azure AI Projects .NET skill describes older SDK guidance. A
  [stable Foundry example](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-ai-projects-dotnet-stable/SKILL.md)
  covers prompt-agent creation for the tested SDK versions. [See the version and compilation review](research-azure-ai-projects-dotnet.md).

- The pinned slides template can advance when Space is pressed on its focused previous button.
  A [maintained template](../included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-slides/SKILL.md)
  addresses tested navigation, scrolling and reduced-motion cases. [See the controls and limits](research-slides-keyboard.md).

- The pinned Anthropic frontend skill uses broad aesthetic rules. [See the
  accessibility and upstream review](research-anthropic-frontend.md).

These examples are not an exhaustive review of the catalog.
The [upstream tree inventory](research-upstream-skill-trees.md) identifies
selected source changes that still require review before adoption.

## Load it in your agent

For an agent that accepts local skill folders, use that agent's documented
configuration to point to the selected folder in your clone. For a file-reading
agent, provide the selected `SKILL.md` path and ask it to read linked resources
as needed. Compact starting points are under
[agent-ready skills](../included/agent-ready/README.md).

Agents using this collection must follow the
[mandatory agent tools](agent-tools.md): Caveman for every task, source-bound
CocoIndex Code before conceptual repository navigation, and Crawl4AI for web-page
research. Keep the local policy and all linked resources accessible. Tool setup
and actual execution receipts are required where those scopes apply; installing
a skill or copying an entrypoint does not prove compliance.

For a fresh code-search provider, follow the
[local CocoIndex setup and search guide](../toolchains/cocoindex-code/README.md).
For public-page research, use the
[Crawl4AI installation guide](../toolchains/crawl4ai/README.md).

Run a small task in your actual agent environment and inspect its output before
depending on broader behaviour. [Read the evidence guide](coverage.md) to
distinguish packaging checks, component tests and agent trials.

## Requirements and troubleshooting

Host-agnostic means no fixed machine, username, installation path or AI client.
Each component keeps its documented operating-system requirements. The qualified
[Crawl4AI](../toolchains/crawl4ai/README.md) and
[local CocoIndex](../toolchains/cocoindex-code/README.md) providers support Windows x64.
Catalog-validation CI also exercises Linux; that does not port the Windows
provider or certify every mirrored skill on Linux.

If a resource link fails, open the skill from the intact clone. If a required
provider is missing or stale, follow [the tool setup policy](agent-tools.md)
and restore it before dependent work. Keep other projects' provider registrations
and caches intact.

For changes to this collection, use the separate
[contributor guide](../CONTRIBUTING.md) and
[development setup](development.md), including reproducible regeneration and
all local quality gates.
