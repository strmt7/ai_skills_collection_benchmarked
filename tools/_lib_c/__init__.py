"""Shared helpers for Batch C evaluator/audit tools.

This package is owned by the Batch C (evaluators) workstream. Other batches
must not import from here to avoid cross-batch coupling. Everything here is
stdlib-only, deterministic, and network-free unless a caller explicitly opts
in via an allow-network flag.
"""

from ._catalog import load_catalog, load_manifest, load_scenarios
from ._diff import DriftReport, describe_data_drift, describe_text_drift
from ._io import load_json, read_text, write_json_canonical, write_text
from ._progress import log_progress, progress_iter
from ._schema import SchemaError, validate_against_schema

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
