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
