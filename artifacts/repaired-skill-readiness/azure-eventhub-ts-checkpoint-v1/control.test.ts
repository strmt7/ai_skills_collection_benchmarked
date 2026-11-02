import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { runInNewContext } from "node:vm";
import type { PartitionContext, ReceivedEventData, SubscriptionEventHandlers } from "@azure/event-hubs";
import { checkpointHandlers } from "./checkpoint-consumer.js";

type Operation = [string, number];
function event(id: number): ReceivedEventData {
  return { body: id } as ReceivedEventData;
}
function context(operations: Operation[], checkpointFails = false): PartitionContext {
  return {
    updateCheckpoint: async (value: ReceivedEventData) => {
      operations.push(["checkpoint", value.body as number]);
      if (checkpointFails) throw new Error("checkpoint failed");
    },
  } as unknown as PartitionContext;
}
const errorHandler: SubscriptionEventHandlers["processError"] = async () => {};

test("all events finish before checkpoint", async () => {
  const operations: Operation[] = [];
  const handler = checkpointHandlers(async (value) => { operations.push(["handled", value.body as number]); }, errorHandler);
  await handler.processEvents([event(1), event(2)], context(operations));
  assert.deepEqual(operations, [["handled", 1], ["handled", 2], ["checkpoint", 2]]);
});

test("empty callback does not checkpoint", async () => {
  const operations: Operation[] = [];
  const handler = checkpointHandlers(async (value) => { operations.push(["handled", value.body as number]); }, errorHandler);
  await handler.processEvents([], context(operations));
  assert.deepEqual(operations, []);
});

test("handler failure propagates and does not checkpoint a partial batch", async () => {
  const operations: Operation[] = [];
  const handler = checkpointHandlers(async (value) => {
    operations.push(["handled", value.body as number]);
    if (value.body === 2) throw new Error("processing failed");
  }, errorHandler);
  await assert.rejects(handler.processEvents([event(1), event(2), event(3)], context(operations)), /processing failed/);
  assert.deepEqual(operations, [["handled", 1], ["handled", 2]]);
});

test("checkpoint failure propagates", async () => {
  const operations: Operation[] = [];
  const handler = checkpointHandlers(async (value) => { operations.push(["handled", value.body as number]); }, errorHandler);
  await assert.rejects(handler.processEvents([event(1)], context(operations, true)), /checkpoint failed/);
  assert.deepEqual(operations, [["handled", 1], ["checkpoint", 1]]);
});

test("original snippet can swallow failure before checkpointing a later batch", async () => {
  const path = process.env.ORIGINAL_SKILL;
  if (!path) throw new Error("ORIGINAL_SKILL is required");
  const source = readFileSync(path, "utf8").replace(/\r\n/g, "\n");
  if (createHash("sha256").update(source).digest("hex") !== "628dd0e1c7ea86baa518db273c43664e4de2ea6f7e3154ac2c01c8174b5d25c3") {
    throw new Error("Original source digest mismatch");
  }
  const body = source.split("## Error Handling")[1]?.split("```typescript")[1]?.split("```")[0];
  if (!body) throw new Error("Original error-handling example not found");
  const operations: Operation[] = [];
  let captured: SubscriptionEventHandlers | undefined;
  const sandbox = {
    consumer: { subscribe: (handlers: SubscriptionEventHandlers) => { captured = handlers; } },
    processEvent: async (value: ReceivedEventData) => {
      operations.push(["handled", value.body as number]);
      if (value.body === 1) throw new Error("processing failed");
    },
    console: { error: () => {}, warn: () => {} },
  };
  runInNewContext(body, sandbox);
  if (!captured) throw new Error("Subscription handler not captured");
  await captured.processEvents([event(1)], context(operations));
  await captured.processEvents([event(2)], context(operations));
  assert.deepEqual(operations, [["handled", 1], ["handled", 2], ["checkpoint", 2]]);
});
