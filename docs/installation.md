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

- The pinned XLSX helpers can misreport simulated timeouts and literal error
  text. [See the recalculation controls](research-xlsx-recalculation.md).
- The pinned docs-from-code fallbacks can miss or misidentify routes, and the
  TypeScript fallback failed to start in the tested environment. [See the extractor controls](research-docs-from-code.md).

These examples are not an exhaustive review of the catalog.

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
