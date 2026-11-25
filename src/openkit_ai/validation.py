"""Validate parsed JSON objects against simple Python type schemas."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


TypeSpec = type | tuple[type, ...]


class JSONValidationError(ValueError):
    """Raised when parsed JSON does not match a requested object schema."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("JSON response validation failed: " + "; ".join(errors))


def validate_json_response(response: str, schema: Mapping[str, TypeSpec]) -> dict[str, Any]:
    """Parse a model response and validate required object fields by Python type.

    The schema maps required field names to a type (or tuple of accepted types).
    Additional object fields are allowed. Nested objects are not recursively
    validated; use a separate validation step for those fields.
    """
    from .json_utils import parse_json_response

    if not isinstance(schema, Mapping):
        raise TypeError("schema must be a mapping of field names to types")

    for field, expected in schema.items():
        if not isinstance(field, str):
            raise TypeError("schema field names must be strings")
        valid_type_spec = isinstance(expected, type) or (
            isinstance(expected, tuple)
            and bool(expected)
            and all(isinstance(item, type) for item in expected)
        )
        if not valid_type_spec:
            raise TypeError(f"schema entry for {field!r} must be a type or non-empty tuple of types")

    data = parse_json_response(response)
    if not isinstance(data, dict):
        raise JSONValidationError(["expected a JSON object at the top level"])

    errors: list[str] = []
    for field, expected in schema.items():
        if field not in data:
            errors.append(f"missing required field {field!r}")
            continue
        value = data[field]
        if not isinstance(value, expected):
            expected_types = expected if isinstance(expected, tuple) else (expected,)
            expected_names = " or ".join(item.__name__ for item in expected_types)
            errors.append(
                f"field {field!r} expected {expected_names}, got {type(value).__name__}"
            )

    if errors:
        raise JSONValidationError(errors)
    return data
