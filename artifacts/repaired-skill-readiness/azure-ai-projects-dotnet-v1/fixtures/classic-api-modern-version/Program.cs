using Azure.AI.Projects;
using Azure.AI.Agents.Persistent;
using Azure.Identity;
var endpoint = new Uri("https://example.invalid/api/projects/demo");
AIProjectClient projectClient = new AIProjectClient(endpoint, new DefaultAzureCredential());
PersistentAgentsClient agentsClient = projectClient.GetPersistentAgentsClient();
