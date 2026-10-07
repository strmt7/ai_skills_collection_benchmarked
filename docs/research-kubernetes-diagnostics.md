# Kubernetes diagnostic package review

All three original `debug-buttercup` resources were read completely: the skill,
failure-pattern reference and diagnostic shell helper. They remain locked to
Trail of Bits commit `e8cc5baf9329ccb491bfa200e82eacbac83b1ead`.
The package path is absent from the fetched research snapshot at
`82fe8226252622fa807643bdca1710901198553a`; this establishes absence at that
snapshot, not the reason for removal or a replacement package. Do not advertise
this frozen package as current upstream guidance. Final routing should place
operational incident diagnosis with infrastructure skills rather than treating
it as a coding-agent test benchmark.

The original workflow usefully distinguishes accumulated restart counts from
recent failures and investigates shared dependencies before individual services.
Its service names, stream names, labels and Helm values are deployment-specific
contracts that must be verified against the actual workload. Report incident
time, context/namespace, pod UID, container name, termination timestamps and
evidence before attributing a cascade to Redis. Similar log messages support a
hypothesis; they do not prove one cause. Kubernetes documents explicit container
selection and pod status inspection in its [pod debugging guide](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/).

The helper indexes only the first container's restart status; other containers
and init containers can fail independently. Its Redis selector takes the first
match without verifying readiness, primary role or authentication. API calls
have no explicit request timeout; `--full` bounds individual log tails but not
the number of pods or total collection duration. Cluster-scoped node metrics
require separate authorization. Suppressing stderr loses RBAC, TLS, transport
and command errors. An unavailable observation must retain its error category
and cannot be converted into an absent resource or a clean bill of health.

Six actual Linux controls run the unchanged helper semantics against an owned
command spy: baseline completion, warning-event permission failure, misreported
Redis/metrics permission failures, absent request timeouts and namespace versus
cluster scope. The first fixture failed before producing a spy log. Its Windows
mirror input has CRLF bytes and its executable spy was staged under a noexec
temporary directory. Its receipt is retained. The corrected fixture applies the
existing canonical LF policy only
to a private copy and uses an injected Bash function invoking a Python spy;
the original mirror and noexec isolation remain intact. UID 65534, networkless
execution, temporary cleanup and owned container cleanup are recorded in
`kubernetes-diagnosis-runtime-controls-v2.json`. These are source-contract
controls, not live Kubernetes validation, independent task scores or agent gains.

The skill labels stream length as pending messages. [Redis XLEN](https://redis.io/docs/latest/commands/xlen/)
counts retained stream entries, while [XPENDING](https://redis.io/docs/latest/commands/xpending/)
inspects a consumer group's delivered-but-unacknowledged entries. Evaluate those
alongside group lag, consumer health and processing throughput. Acknowledging
orphaned entries without successful processing can discard work; recovery needs
the application's ownership, delivery and idempotency contracts.

The failure reference proposes memory-backed Redis storage, global Docker
pruning, shorter retention and acknowledging orphaned messages. Those changes
can lose persistence, images, evidence or queued work. Memory-backed storage
also consumes memory and can contribute to pressure. Kubernetes documents that
[emptyDir data is deleted when its pod is removed](https://kubernetes.io/docs/concepts/storage/volumes/).
Verify the chart's storage contract and recovery requirements before proposing
such changes. Prefer bounded collection and preserve current evidence; remediation
must follow the user's existing authorization and the diagnosed failure.

Research remains in progress pending live-compatible collector qualification,
current deployment/source disposition and independent incident-diagnosis tasks.
No cluster, owner repository, Redis data or shared Docker workload was changed.
