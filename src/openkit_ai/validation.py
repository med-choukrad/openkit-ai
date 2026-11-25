"""Validate parsed JSON objects against simple Python type schemas."""

from collections.abc import Mapping

TypeSpec = type | tuple[type, ...] | Mapping[str, object]


class JSONValidationError(ValueError):
    """Raised when parsed JSON does not match a requested object schema."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("JSON response validation failed: " + "; ".join(errors))


def _validate_schema(schema: Mapping[str, object], path: str = "") -> None:
    for field, expected in schema.items():
        if not isinstance(field, str):
            raise TypeError("schema field names must be strings")
        field_path = f"{path}.{field}" if path else field
        if isinstance(expected, Mapping):
            _validate_schema(expected, field_path)
        elif isinstance(expected, type) or (
            isinstance(expected, tuple)
            and expected
            and all(isinstance(item, type) for item in expected)
        ):
            continue
        else:
            raise TypeError(
                f"schema entry for {field_path!r} must be a type, "
                "a non-empty tuple of types, or a nested mapping"
            )


def _collect_errors(
    data: Mapping[str, object],
    schema: Mapping[str, object],
    path: str = "",
) -> list[str]:
    errors: list[str] = []
    for field, expected in schema.items():
        field_path = f"{path}.{field}" if path else field
        if field not in data:
            errors.append(f"missing required field {field_path!r}")
            continue

        value = data[field]
        if isinstance(expected, Mapping):
            if not isinstance(value, dict):
                errors.append(
                    f"field {field_path!r} expected object, got {type(value).__name__}"
                )
            else:
                errors.extend(_collect_errors(value, expected, field_path))
        elif not isinstance(value, expected):
            expected_types = expected if isinstance(expected, tuple) else (expected,)
            expected_names = " or ".join(item.__name__ for item in expected_types)
            errors.append(
                f"field {field_path!r} expected {expected_names}, got {type(value).__name__}"
            )
    return errors


def validate_json_response(
    response: str,
    schema: Mapping[str, object],
) -> dict[str, object]:
    """Parse a model response and validate required fields by Python type.

    Nested mappings validate required fields in nested JSON objects. Additional
    object fields are allowed at every level.
    """
    from .json_utils import parse_json_response

    if not isinstance(schema, Mapping):
        raise TypeError("schema must be a mapping of field names to types")

    _validate_schema(schema)
    data = parse_json_response(response)
    if not isinstance(data, dict):
        raise JSONValidationError(["expected a JSON object at the top level"])

    errors = _collect_errors(data, schema)
    if errors:
        raise JSONValidationError(errors)
    return data
