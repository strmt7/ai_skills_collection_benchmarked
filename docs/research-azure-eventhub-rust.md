# Rust Event Hubs batching

The [pinned Rust skill](../included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-rust/SKILL.md)
uses `try_add_event_data(...)?` without inspecting the returned boolean. The
[SDK documentation](https://docs.rs/azure_messaging_eventhubs/0.15.0/azure_messaging_eventhubs/struct.EventDataBatch.html)
states that `false` means the event did not fit. Ignoring it can omit the
rejected event when examples are adapted to larger inputs.

On 2 November 2026, Cargo 1.99.1 could not resolve the then-current stable
`azure_messaging_eventhubs` 0.16.0 and `azure_identity` 1.0.0 together: their
`azure_core` requirements selected incompatible versions. A separate
[locked example](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-rust-batching/SKILL.md)
using Event Hubs 0.15.0 and identity 1.0.0 compiled locally. It handles a full
batch and an event too large for an empty batch. Package compatibility is a
dated observation and must be rechecked for the actual project.

Compilation did not run the example or connect to Azure, and does not prove
batch delivery, retry behavior, or agent effectiveness. The original mirror is
unchanged. The [qualification record](../artifacts/repaired-skill-readiness/azure-eventhub-rust-batching-v1/qualification.json)
and retained native registry and compiler streams describe the tested scope.

One clean Windows build in a deeply nested evidence directory failed when the
native compiler could not open dependency headers that existed on disk. The
same locked project compiled from an isolated system temporary directory. This
does not establish compatibility with every Windows path or toolchain setup;
the failed and successful build streams are retained separately.
