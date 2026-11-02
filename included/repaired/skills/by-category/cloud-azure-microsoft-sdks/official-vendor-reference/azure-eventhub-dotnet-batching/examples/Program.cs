using Azure.Identity;
using Azure.Messaging.EventHubs;
using Azure.Messaging.EventHubs.Producer;

string fullyQualifiedNamespace = Environment.GetEnvironmentVariable("EVENT_HUB_FULLY_QUALIFIED_NAMESPACE")
    ?? throw new InvalidOperationException("Set EVENT_HUB_FULLY_QUALIFIED_NAMESPACE.");
string eventHubName = Environment.GetEnvironmentVariable("EVENT_HUB_NAME")
    ?? throw new InvalidOperationException("Set EVENT_HUB_NAME.");

await using var producer = new EventHubProducerClient(fullyQualifiedNamespace, eventHubName, new DefaultAzureCredential());
EventData[] events = [new EventData(BinaryData.FromString("event 1")), new EventData(BinaryData.FromString("event 2"))];
int index = 0;
while (index < events.Length)
{
    using EventDataBatch batch = await producer.CreateBatchAsync();
    while (index < events.Length && batch.TryAdd(events[index]))
    {
        index++;
    }
    if (batch.Count == 0)
    {
        throw new InvalidOperationException("An event is too large for an empty batch.");
    }
    await producer.SendAsync(batch);
}
