"""Validate parsed JSON objects against simple Python type schemas."""

from collections.abc import Mapping
from typing import TypeAlias

TypeSpec: TypeAlias = type | tuple[type, ...] | Mapping[str, "TypeSpec"] | list["TypeSpec"]


class JSONValidationError(ValueError):
    """Raised when parsed JSON does not match a requested object schema."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("JSON response validation failed: " + "; ".join(errors))


def _validate_type_spec(expected: object, path: str) -> None:
    if isinstance(expected, Mapping):
        for field, nested in expected.items():
            if not isinstance(field, str):
                raise TypeError("schema field names must be strings")
            _validate_type_spec(nested, f"{path}.{field}" if path else field)
    elif isinstance(expected, list):
        if len(expected) != 1:
            raise TypeError(f"array schema for {path!r} must contain exactly one item schema")
        _validate_type_spec(expected[0], f"{path}[0]")
    elif isinstance(expected, type) or (
        isinstance(expected, tuple)
        and expected
        and all(isinstance(item, type) for item in expected)
    ):
        return
    else:
        raise TypeError(
            f"schema entry for {path!r} must be a type, a non-empty tuple of types, "
            "a nested mapping, or a list containing exactly one item schema"
        )


def _validate_schema(schema: Mapping[str, object]) -> None:
    for field, expected in schema.items():
        if not isinstance(field, str):
            raise TypeError("schema field names must be strings")
        _validate_type_spec(expected, field)


def _matches_expected_type(value: object, expected: type | tuple[type, ...]) -> bool:
    types = expected if isinstance(expected, tuple) else (expected,)
    # bool is a subclass of int in Python, but JSON booleans are not JSON numbers.
    if isinstance(value, bool) and int in types and bool not in types:
        types = tuple(item for item in types if item is not int)
    return any(isinstance(value, item) for item in types)


def _collect_value_errors(value: object, expected: object, path: str, strict: bool) -> list[str]:
    if isinstance(expected, Mapping):
        if not isinstance(value, dict):
            return [f"field {path!r} expected object, got {type(value).__name__}"]
        return _collect_errors(value, expected, path, strict)
    if isinstance(expected, list):
        if not isinstance(value, list):
            return [f"field {path!r} expected array, got {type(value).__name__}"]
        errors: list[str] = []
        for index, item in enumerate(value):
            errors.extend(_collect_value_errors(item, expected[0], f"{path}[{index}]", strict))
        return errors
    if not _matches_expected_type(value, expected):
        types = expected if isinstance(expected, tuple) else (expected,)
        names = " or ".join(item.__name__ for item in types)
        return [f"field {path!r} expected {names}, got {type(value).__name__}"]
    return []


def _collect_errors(
    data: Mapping[str, object],
    schema: Mapping[str, object],
    path: str = "",
    strict: bool = False,
) -> list[str]:
    errors: list[str] = []
    if strict:
        for field in data:
            if field not in schema:
                field_path = f"{path}.{field}" if path else field
                errors.append(f"unexpected field {field_path!r}")
    for field, expected in schema.items():
        field_path = f"{path}.{field}" if path else field
        if field not in data:
            errors.append(f"missing required field {field_path!r}")
        else:
            errors.extend(_collect_value_errors(data[field], expected, field_path, strict))
    return errors


def validate_json_response(
    response: str, schema: Mapping[str, TypeSpec], *, strict: bool = False
) -> dict[str, object]:
    """Parse JSON and validate required fields against recursive type schemas.

    Use [str] for arrays of strings, [{"name": str}] for arrays of objects,
    and nested forms such as [[int]] for arrays of arrays. Each list schema
    must contain exactly one item schema. Additional object fields are allowed
    by default; pass strict=True to reject undeclared fields at every object level.
    Booleans are not accepted as integers unless bool is explicitly allowed.
    """
    from .json_utils import parse_json_response

    if not isinstance(strict, bool):
        raise TypeError("strict must be a bool")
    if not isinstance(schema, Mapping):
        raise TypeError("schema must be a mapping of field names to types")
    _validate_schema(schema)
    data = parse_json_response(response)
    if not isinstance(data, dict):
        raise JSONValidationError(["expected a JSON object at the top level"])
    errors = _collect_errors(data, schema, strict=strict)
    if errors:
        raise JSONValidationError(errors)
    return data
