# Durable job boundaries

Define what acceptance means. If a database change obligates the service to do
follow-up work, persist the change and a job or outbox record in the same
transaction. Send the acceptance response after commit. For a repeated request,
look up its scoped idempotency key and compare the normalized payload. Return
the original job identity for the same request and the declared conflict
response for a different payload.

Claim eligible work in a short transaction. Store an owner or a monotonically
increasing claim generation and a deadline. Check the claim again when renewing
or completing it. A resumed worker can hold an expired claim while another
worker processes the same job. Use database-backed time or an explicit shared
clock contract for deadlines and delayed retries. Choose a stable ordering for
queue eligibility and make the retry and dead-letter policy explicit.

If the queue and effect share a database, commit the effect and completion
together. For a remote effect, use a stable operation key and the receiving
system's documented idempotency or reconciliation workflow. An outbox relay can
retry publication after it loses an acknowledgement. Record terminal failures
and surface jobs that exceed their delivery budget.

Test these events through the real request and worker entrypoints:

- The request stops before commit. Neither the business change nor the job
  becomes visible.
- The request stops after commit and before responding. A retry locates the
  original job and a conflicting payload receives the declared response.
- A worker stops before committing its effect. Another worker reclaims the
  job after the deadline, and stale completion is rejected.
- A worker stops after committing its effect. Recovery observes the recorded
  completion or reconciles the remote effect before retrying it.

Choose the claim mechanism for the actual database. For PostgreSQL workers,
`FOR UPDATE SKIP LOCKED` can avoid waiting on rows already held by another
worker. A concurrent claim can skip earlier rows, so specify delivery ordering
separately from the ordering of eligible rows.
[PostgreSQL SELECT locking clauses](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
