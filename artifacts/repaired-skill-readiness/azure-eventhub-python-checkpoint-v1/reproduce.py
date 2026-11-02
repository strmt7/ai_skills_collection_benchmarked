"""Exercise a synchronous Event Hubs checkpoint example without service access."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
import unittest
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

from azure.eventhub import EventData, EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXAMPLE = ROOT / (
    "included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/"
    "azure-eventhub-python-checkpoint/examples/checkpoint_consumer.py"
)
EXPECTED = {
    "azure-eventhub": "5.15.1",
    "azure-eventhub-checkpointstoreblob": "1.2.0",
    "azure-identity": "1.27.0",
}


class NeverCredential:
    def get_token(self, *args, **kwargs):
        raise AssertionError("A token must not be requested by the offline control")


class Context:
    def __init__(self, operations, fail=False):
        self.operations = operations
        self.fail = fail

    def update_checkpoint(self, event):
        self.operations.append(("checkpoint", event))
        if self.fail:
            raise RuntimeError("checkpoint failed")


class CheckpointControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("eventhub_checkpoint_example", EXAMPLE)
        if spec is None or spec.loader is None:
            raise RuntimeError("Cannot load checkpoint example")
        cls.module = importlib.util.module_from_spec(spec)
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            spec.loader.exec_module(cls.module)
        finally:
            sys.dont_write_bytecode = previous

    def run_receive(self, handler, callback):
        def on_error(context, error):
            pass

        def simulated_receive(client, *, on_event, starting_position, max_wait_time, on_error):
            self.assertIsInstance(client, EventHubConsumerClient)
            self.assertEqual(starting_position, "-1")
            self.assertEqual(max_wait_time, 1.0)
            self.assertIs(on_error, error_handler)
            callback(on_event)

        error_handler = on_error
        with (
            patch.object(EventHubConsumerClient, "receive", autospec=True, side_effect=simulated_receive) as receive,
            self.module.open_checkpoint_consumer(
                credential=NeverCredential(),
                namespace="example.servicebus.windows.net",
                eventhub_name="example",
                consumer_group="test-group",
                blob_account_url="https://example.blob.core.windows.net",
                container_name="test-checkpoints",
            ) as consumer,
        ):
            consumer.receive(
                on_event=self.module.checkpoint_after_handling(handler),
                starting_position="-1",
                max_wait_time=1.0,
                on_error=error_handler,
            )
        self.assertEqual(receive.call_count, 1)

    def test_handler_finishes_before_checkpoint(self):
        operations = []
        event = EventData("example")
        context = Context(operations)
        self.run_receive(lambda value: operations.append(("handled", value)), lambda callback: callback(context, event))
        self.assertEqual(operations, [("handled", event), ("checkpoint", event)])

    def test_no_event_is_not_handled_or_checkpointed(self):
        operations = []
        self.run_receive(
            lambda value: operations.append(("handled", value)), lambda callback: callback(Context(operations), None)
        )
        self.assertEqual(operations, [])

    def test_handler_failure_does_not_checkpoint(self):
        operations = []

        def fail_handler(event):
            operations.append(("handler failed", event))
            raise RuntimeError("handler failed")

        event = EventData("example")
        with self.assertRaisesRegex(RuntimeError, "handler failed"):
            self.run_receive(fail_handler, lambda callback: callback(Context(operations), event))
        self.assertEqual(operations, [("handler failed", event)])

    def test_checkpoint_failure_is_not_silenced(self):
        operations = []
        event = EventData("example")
        with self.assertRaisesRegex(RuntimeError, "checkpoint failed"):
            self.run_receive(
                lambda value: operations.append(("handled", value)),
                lambda callback: callback(Context(operations, fail=True), event),
            )
        self.assertEqual(operations, [("handled", event), ("checkpoint", event)])

    def test_clients_close_when_handler_fails(self):
        consumer_close = EventHubConsumerClient.close
        store_exit = BlobCheckpointStore.__exit__

        def fail_handler(event):
            raise RuntimeError("handler failed")

        with (
            patch.object(EventHubConsumerClient, "close", autospec=True, side_effect=consumer_close) as close_consumer,
            patch.object(BlobCheckpointStore, "__exit__", autospec=True, side_effect=store_exit) as exit_store,
            self.assertRaisesRegex(RuntimeError, "handler failed"),
        ):
            self.run_receive(fail_handler, lambda callback: callback(Context([]), EventData("example")))
        self.assertEqual(close_consumer.call_count, 1)
        self.assertEqual(exit_store.call_count, 1)

    def test_store_closes_when_consumer_construction_fails(self):
        store_exit = BlobCheckpointStore.__exit__
        with (
            patch.object(BlobCheckpointStore, "__exit__", autospec=True, side_effect=store_exit) as exit_store,
            patch.object(self.module, "EventHubConsumerClient", side_effect=RuntimeError("consumer init failed")),
            self.assertRaisesRegex(RuntimeError, "consumer init failed"),
            self.module.open_checkpoint_consumer(
                credential=NeverCredential(),
                namespace="example.servicebus.windows.net",
                eventhub_name="example",
                consumer_group="test-group",
                blob_account_url="https://example.blob.core.windows.net",
                container_name="test-checkpoints",
            ),
        ):
            self.fail("Consumer construction should fail")
        self.assertEqual(exit_store.call_count, 1)


def main() -> int:
    observed = {name: version(name) for name in EXPECTED}
    if observed != EXPECTED:
        raise ValueError(f"Unexpected package versions: {observed}")
    with patch("socket.socket.connect", side_effect=AssertionError("Network access is forbidden in the control")):
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(CheckpointControls)
        )
    report = {
        "schema_version": 1,
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "packages": observed,
        "example_sha256": hashlib.sha256(EXAMPLE.read_bytes()).hexdigest(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "azure_service_called": False,
        "agent_performance_tested": False,
    }
    print(json.dumps(report, indent=2))
    return 0 if result.wasSuccessful() and result.testsRun == 6 else 1


if __name__ == "__main__":
    sys.exit(main())
