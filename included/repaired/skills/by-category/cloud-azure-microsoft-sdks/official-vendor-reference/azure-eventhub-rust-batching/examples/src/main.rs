use azure_identity::DeveloperToolsCredential;
use azure_messaging_eventhubs::ProducerClient;
use std::error::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let namespace = std::env::var("EVENT_HUB_FULLY_QUALIFIED_NAMESPACE")?;
    let eventhub_name = std::env::var("EVENT_HUB_NAME")?;
    let credential = DeveloperToolsCredential::new(None)?;
    let producer = ProducerClient::builder()
        .open(&namespace, &eventhub_name, credential)
        .await?;
    let events = [b"event 1".to_vec(), b"event 2".to_vec()];
    let mut batch = producer.create_batch(None).await?;

    for payload in events {
        if !batch.try_add_event_data(payload.clone(), None)? {
            if batch.is_empty() {
                return Err("event is too large for an empty batch".into());
            }
            producer.send_batch(batch, None).await?;
            batch = producer.create_batch(None).await?;
            if !batch.try_add_event_data(payload, None)? {
                return Err("event is too large for an empty batch".into());
            }
        }
    }
    if batch.is_empty() {
        drop(batch);
    } else {
        producer.send_batch(batch, None).await?;
    }
    producer.close().await?;
    Ok(())
}
