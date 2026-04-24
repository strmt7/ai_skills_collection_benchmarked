"""Shared helpers for Batch C evaluator/audit tools.

This package is owned by the Batch C (evaluators) workstream. Other batches
must not import from here to avoid cross-batch coupling. Everything here is
stdlib-only, deterministic, and network-free unless a caller explicitly opts
in via an allow-network flag.
"""

from ._io import load_json, write_json_canonical, read_text, write_text
from ._diff import describe_data_drift, describe_text_drift, DriftReport
from ._progress import progress_iter, log_progress
from ._schema import validate_against_schema, SchemaError
from ._catalog import load_catalog, load_manifest, load_scenarios

__all__ = [
    "load_json",
    "write_json_canonical",
    "read_text",
    "write_text",
    "describe_data_drift",
    "describe_text_drift",
    "DriftReport",
    "progress_iter",
    "log_progress",
    "validate_against_schema",
    "SchemaError",
    "load_catalog",
    "load_manifest",
    "load_scenarios",
]
