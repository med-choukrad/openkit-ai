"""Validate parsed JSON objects against simple Python type schemas."""

import types
import typing
from collections.abc import Mapping
from enum import Enum
from typing import Any, Literal, TypeAlias, Union, get_args, get_origin, get_type_hints

TypeSpec: TypeAlias = (
    type
    | tuple[type, ...]
    | Mapping[str, "TypeSpec"]
    | list["TypeSpec"]
    | types.UnionType
    | Any
)


class JSONValidationError(ValueError):
    """Raised when parsed JSON does not match a requested object schema."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("JSON response validation failed: " + "; ".join(errors))


def _is_typed_dict(expected: object) -> bool:
    return isinstance(expected, type) and typing.is_typeddict(expected)


def _typed_dict_hints(expected: type) -> dict[str, object]:
    try:
        return get_type_hints(expected, include_extras=True)
    except (NameError, TypeError):
        return dict(expected.__annotations__)


def _required_typed_dict_fields(expected: type) -> set[str]:
    hints = _typed_dict_hints(expected)
    required = set(expected.__required_keys__)
    optional = set(expected.__optional_keys__)
    for field, annotation in hints.items():
        wrapper_name = getattr(get_origin(annotation), "__name__", "")
        if wrapper_name == "Required":
            required.add(field)
            optional.discard(field)
        elif wrapper_name == "NotRequired":
            optional.add(field)
            required.discard(field)
    return required


def _unwrap_required(expected: object) -> object:
    if get_origin(expected) in (typing.Required, typing.NotRequired):
        return get_args(expected)[0]
    return expected


def _union_args(expected: object) -> tuple[object, ...]:
    origin = get_origin(expected)
    if origin in (Union, types.UnionType):
        return get_args(expected)
    return ()


def _literal_args(expected: object) -> tuple[object, ...]:
    if get_origin(expected) is Literal:
        return get_args(expected)
    return ()


def _is_enum_type(expected: object) -> bool:
    return isinstance(expected, type) and issubclass(expected, Enum)


def _validate_type_spec(expected: object, path: str) -> None:
    expected = _unwrap_required(expected)
    if _is_typed_dict(expected):
        for field, nested in _typed_dict_hints(expected).items():
            _validate_type_spec(nested, f"{path}.{field}" if path else field)
    elif isinstance(expected, Mapping):
        for field, nested in expected.items():
            if not isinstance(field, str):
                raise TypeError("schema field names must be strings")
            _validate_type_spec(nested, f"{path}.{field}" if path else field)
    elif get_origin(expected) is list:
        _validate_type_spec(get_args(expected)[0], f"{path}[0]")
    elif isinstance(expected, list):
        if len(expected) != 1:
            raise TypeError(f"array schema for {path!r} must contain exactly one item schema")
        _validate_type_spec(expected[0], f"{path}[0]")
    elif _union_args(expected):
        for option in _union_args(expected):
            _validate_type_spec(option, path)
    elif _literal_args(expected):
        values = _literal_args(expected)
        if not all(value is None or isinstance(value, (str, int, float, bool)) for value in values):
            raise TypeError(f"Literal schema for {path!r} must contain JSON scalar values")
    elif _is_enum_type(expected) or isinstance(expected, type) or (
        isinstance(expected, tuple)
        and expected
        and all(isinstance(item, type) for item in expected)
    ):
        return
    else:
        raise TypeError(
            f"schema entry for {path!r} must be a type, a non-empty tuple of types, "
            "a type union, a nested mapping, or a list containing exactly one item schema"
        )


def _validate_schema(schema: Mapping[str, object] | type) -> None:
    if _is_typed_dict(schema):
        _validate_type_spec(schema, "")
        return
    for field, expected in schema.items():
        if not isinstance(field, str):
            raise TypeError("schema field names must be strings")
        _validate_type_spec(expected, field)


def _literal_value_matches(value: object, literal: object) -> bool:
    if type(value) is not type(literal):
        return False
    return value == literal


def _matches_expected_type(value: object, expected: object) -> bool:
    expected = _unwrap_required(expected)
    union_options = _union_args(expected)
    if union_options:
        return any(_matches_expected_type(value, option) for option in union_options)

    literal_values = _literal_args(expected)
    if literal_values:
        return any(_literal_value_matches(value, option) for option in literal_values)

    if _is_enum_type(expected):
        return any(_literal_value_matches(value, member.value) for member in expected)

    types_to_check = expected if isinstance(expected, tuple) else (expected,)
    # bool is a subclass of int in Python, but JSON booleans are not JSON numbers.
    if isinstance(value, bool) and int in types_to_check and bool not in types_to_check:
        types_to_check = tuple(item for item in types_to_check if item is not int)
    return any(isinstance(value, item) for item in types_to_check)


def _expected_type_names(expected: object) -> str:
    union_options = _union_args(expected)
    if union_options:
        return " or ".join(_expected_type_names(option) for option in union_options)
    literal_values = _literal_args(expected)
    if literal_values:
        return f"Literal{literal_values!r}"
    if _is_enum_type(expected):
        return expected.__name__
    types_to_check = expected if isinstance(expected, tuple) else (expected,)
    return " or ".join(item.__name__ for item in types_to_check)


def _collect_value_errors(value: object, expected: object, path: str, strict: bool) -> list[str]:
    expected = _unwrap_required(expected)
    if _is_typed_dict(expected):
        if not isinstance(value, dict):
            return [f"field {path!r} expected object, got {type(value).__name__}"]
        return _collect_typed_dict_errors(
            value, expected, _typed_dict_hints(expected), path, strict
        )
    if isinstance(expected, Mapping):
        if not isinstance(value, dict):
            return [f"field {path!r} expected object, got {type(value).__name__}"]
        return _collect_errors(value, expected, path, strict)
    if get_origin(expected) is list:
        if not isinstance(value, list):
            return [f"field {path!r} expected array, got {type(value).__name__}"]
        item_schema = get_args(expected)[0]
        errors: list[str] = []
        for index, item in enumerate(value):
            errors.extend(_collect_value_errors(item, item_schema, f"{path}[{index}]", strict))
        return errors
    if isinstance(expected, list):
        if not isinstance(value, list):
            return [f"field {path!r} expected array, got {type(value).__name__}"]
        errors: list[str] = []
        for index, item in enumerate(value):
            errors.extend(_collect_value_errors(item, expected[0], f"{path}[{index}]", strict))
        return errors
    if not _matches_expected_type(value, expected):
        message = (
            f"field {path!r} expected {_expected_type_names(expected)}, "
            f"got {type(value).__name__}"
        )
        return [message]
    return []


def _collect_typed_dict_errors(
    data: Mapping[str, object],
    typed_dict: type,
    schema: Mapping[str, object],
    path: str,
    strict: bool,
) -> list[str]:
    errors: list[str] = []
    if strict:
        for field in data:
            if field not in schema:
                field_path = f"{path}.{field}" if path else field
                errors.append(f"unexpected field {field_path!r}")
    required = _required_typed_dict_fields(typed_dict)
    for field, expected in schema.items():
        field_path = f"{path}.{field}" if path else field
        if field not in data:
            if field in required:
                errors.append(f"missing required field {field_path!r}")
        else:
            errors.extend(_collect_value_errors(data[field], expected, field_path, strict))
    return errors


def _collect_errors(
    data: Mapping[str, object],
    schema: Mapping[str, object] | type,
    path: str = "",
    strict: bool = False,
) -> list[str]:
    if _is_typed_dict(schema):
        return _collect_typed_dict_errors(
            data, schema, _typed_dict_hints(schema), path, strict
        )
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
    response: str, schema: Mapping[str, TypeSpec] | type, *, strict: bool = False
) -> dict[str, object]:
    """Parse JSON and validate required fields against recursive type schemas.

    Use [str] for arrays of strings, [{"name": str}] for arrays of objects,
    and nested forms such as [[int]] for arrays of arrays. Use str | None or
    Optional[str] to allow JSON null. Use Literal["draft", "published"] or an
    Enum class to restrict values, or a TypedDict class for object schemas.
    Additional object fields are allowed by
    default; pass strict=True to reject undeclared fields at every object level.
    Booleans are not accepted as integers unless bool is explicitly allowed.
    """
    from .json_utils import parse_json_response

    if not isinstance(strict, bool):
        raise TypeError("strict must be a bool")
    if not isinstance(schema, Mapping) and not _is_typed_dict(schema):
        raise TypeError("schema must be a mapping of field names to types or a TypedDict")
    _validate_schema(schema)
    data = parse_json_response(response)
    if not isinstance(data, dict):
        raise JSONValidationError(["expected a JSON object at the top level"])
    errors = _collect_errors(data, schema, strict=strict)
    if errors:
        raise JSONValidationError(errors)
    return data
