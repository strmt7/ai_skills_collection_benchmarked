---
name: azure-ai-projects-dotnet-stable
description: Use the Azure AI Projects .NET SDK to create a prompt agent in a current Foundry project; distinguish it from Foundry classic projects.
license: MIT
---

# Azure AI Projects for .NET

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and its linked skills, retaining the required receipts.

First identify whether the target is a current Microsoft Foundry project or a
Foundry classic project. Existing applications may rely on the classic API;
do not migrate them solely because a newer SDK exists. Check the current
[Microsoft SDK overview](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview)
and the project's deployment and package constraints before selecting versions.
The older `Azure.AI.Projects.OpenAI` preview extension and the stable
`Azure.AI.Extensions.OpenAI` extension must not be installed together; see the
SDK overview. The pinned upstream versioned-agent example uses the former and
does not compile with the current package combination tested in this repository.

For a new Foundry project, [the example](examples/Program.cs) creates a prompt
agent version with the stable `Azure.AI.Projects.Agents` API. The accompanying
[project](examples/Example.csproj) and [lock file](examples/packages.lock.json)
record the .NET 10 and NuGet versions used for the compile control. Adapt the
target framework, deployment name, package versions and lifecycle to the real
project. Restore the example with `dotnet restore --locked-mode` and compile it
with `dotnet build --no-restore` from the example directory.

Running the example requires a Foundry project endpoint, an authorized identity,
a model deployment, and the `PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME` and
`AGENT_NAME` environment variables. It creates an agent version in the service;
manage its lifecycle according to the user's task and account. Compilation alone
does not verify Azure access, model availability, service behavior or costs.
For conversations, tools, evaluation or classic projects, consult the relevant
current Microsoft documentation and test the actual project rather than assuming
the example covers them.

The original skill is retained in `provenance/`. This narrow overlay is not a
complete review of the source skill or an agent-effectiveness benchmark.
