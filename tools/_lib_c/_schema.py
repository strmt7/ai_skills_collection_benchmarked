"""Minimal stdlib JSON-Schema validator for ``required``/``type``/``const``.

The existing evaluators bundle their own JSON schemas under ``evaluators/``.
Adding a hard dependency on ``jsonschema`` would change the install surface,
so this module implements the tiny subset the schemas actually use:

* ``type``                (``object``, ``array``, ``string``, ``number``,
  ``integer``, ``boolean``, ``null``)
* ``required`` fields on objects
* ``properties`` with recursive validation
* ``items`` and ``minItems`` on arrays
* ``const``
* ``additionalProperties`` honoured only in the ``False`` case

Anything outside this subset is treated as a pass-through so schemas remain
forward-compatible. The goal is not to replace ``jsonschema``; it is to give
Batch-C tools a deterministic offline structural check.
"""

from __future__ import annotations

from typing import Any


class SchemaError(ValueError):
    """Raised when a JSON document fails the supported-schema subset."""


_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "null": (type(None),),
}


def _validate(instance: Any, schema: Any, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(schema, dict):
        return errors
    expected_type = schema.get("type")
    if expected_type:
        types = _TYPE_MAP.get(expected_type)
        if types is None:
            return errors
        # bool is a subclass of int; reject it where ``number``/``integer`` is expected
        if expected_type in {"integer", "number"} and isinstance(instance, bool):
            errors.append(f"{path or '<root>'}: expected {expected_type}, got boolean")
        elif not isinstance(instance, types):
            errors.append(
                f"{path or '<root>'}: expected {expected_type}, got {type(instance).__name__}"
            )
            return errors
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path or '<root>'}: expected const {schema['const']!r}, got {instance!r}")
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path or '<root>'}: required property '{key}' is missing")
        properties = schema.get("properties", {})
        for key, sub_schema in properties.items():
            if key in instance:
                errors.extend(_validate(instance[key], sub_schema, f"{path}.{key}" if path else key))
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            for key in instance:
                if key not in allowed:
                    errors.append(f"{path or '<root>'}: additional property '{key}' not permitted")
    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(instance) < min_items:
            errors.append(f"{path or '<root>'}: expected at least {min_items} items, got {len(instance)}")
        items_schema = schema.get("items")
        if items_schema is not None:
            for idx, item in enumerate(instance):
                errors.extend(_validate(item, items_schema, f"{path}[{idx}]"))
    return errors


def validate_against_schema(instance: Any, schema: dict[str, Any]) -> list[str]:
    """Return a sorted list of human-readable validation errors; empty on pass."""

    return sorted(set(_validate(instance, schema, "")))
