using Azure.AI.Projects;
using Azure.AI.Projects.OpenAI;
using Azure.Identity;
using OpenAI.Responses;
var endpoint = new Uri("https://example.invalid/api/projects/demo");
AIProjectClient projectClient = new(endpoint, new DefaultAzureCredential());
PromptAgentDefinition agentDefinition = new(model: "deployment") { Instructions = "Hello" };
AgentVersion agentVersion = await projectClient.Agents.CreateAgentVersionAsync(agentName: "demo", options: new(agentDefinition));
ProjectResponsesClient responseClient = projectClient.OpenAI.GetProjectResponsesClientForAgent(agentVersion.Name);
