# Azure AI Projects for .NET

The pinned [Azure AI Projects skill](../included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-ai-projects-dotnet/SKILL.md)
describes 1.1.0 as the current stable version and recommends a preview extension
for versioned agents. On 1 November 2026, NuGet's version index listed 2.0.1 as
the latest stable `Azure.AI.Projects` release. Microsoft distinguishes [Foundry
and Foundry classic SDKs](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview)
and says not to install the older preview `Azure.AI.Projects.OpenAI` extension
alongside the stable `Azure.AI.Extensions.OpenAI` extension. Select the API for
the actual project; a newer major version is not an automatic migration plan.

An isolated .NET SDK 10.0.403 compile control adapted two calls from the pinned
versioned-agent example. It compiled with `Azure.AI.Projects` 1.2.0-beta.5 and
`Azure.AI.Projects.OpenAI` 1.0.0-beta.5 after explicitly opting into preview
features. With `Azure.AI.Projects` 2.0.1 and `Azure.AI.Projects.OpenAI`
2.0.0-beta.1, the same source failed because the `AIProjectClient.Agents` and
`AIProjectClient.OpenAI` members were unavailable. The older preview build
without the opt-in also failed on preview-feature diagnostics. These are the
specific tested package combinations, not a claim about every 1.x or 2.x API.

In a separate control, the pinned skill's basic persistent-agent client call
compiled with Projects 1.1.0 and with 2.0.1. A [maintained stable example](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-ai-projects-dotnet-stable/SKILL.md)
uses the [current prompt-agent API](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent)
and compiled with warnings treated as errors. Its locked project records the
tested dependency graph. The checks did not execute the programs, connect to
Azure, or establish an agent benchmark improvement.

The pinned and observed upstream skill files have different Git blob IDs; the
selected installation and versioned-agent guidance was still present in the
observed file. The original mirror is unchanged. [Component evidence](../artifacts/repaired-skill-readiness/azure-ai-projects-dotnet-v1/qualification.json)
records hashes and exact observations; native package indexes, command streams
and web captures remain outside Git.
