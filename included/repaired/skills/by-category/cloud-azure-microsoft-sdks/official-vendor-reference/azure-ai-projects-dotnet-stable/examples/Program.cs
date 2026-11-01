using Azure.Identity;
using Azure.AI.Projects;
using Azure.AI.Projects.Agents;
using Azure.AI.Extensions.OpenAI;

string endpoint = Environment.GetEnvironmentVariable("PROJECT_ENDPOINT") ?? throw new InvalidOperationException("PROJECT_ENDPOINT is required");
string deployment = Environment.GetEnvironmentVariable("MODEL_DEPLOYMENT_NAME") ?? throw new InvalidOperationException("MODEL_DEPLOYMENT_NAME is required");
string agentName = Environment.GetEnvironmentVariable("AGENT_NAME") ?? throw new InvalidOperationException("AGENT_NAME is required");
AIProjectClient projectClient = new(endpoint: new Uri(endpoint), tokenProvider: new DefaultAzureCredential());
ProjectsAgentDefinition definition = new DeclarativeAgentDefinition(deployment) { Instructions = "Answer the user's question." };
ProjectsAgentVersion agent = projectClient.AgentAdministrationClient.CreateAgentVersion(agentName, options: new(definition));
Console.WriteLine($"Agent: {agent.Name}, version: {agent.Version}");
