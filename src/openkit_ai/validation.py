"""Validate parsed JSON objects against simple Python type schemas."""

import math
import sys
import types
import typing
from collections.abc import Mapping
from enum import Enum
from typing import Any, Literal, TypeAlias, Union, get_args, get_origin, get_type_hints

TypeSpec: TypeAlias = (
    type
    | tuple["TypeSpec", ...]
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
    if not isinstance(expected, type):
        return False
    is_typeddict = getattr(typing, "is_typeddict", None)
    if is_typeddict is not None and is_typeddict(expected):
        return True
    # typing_extensions.TypedDict on Python 3.10 uses its own metaclass.
    return (
        type(expected).__name__ == "_TypedDictMeta"
        and hasattr(expected, "__required_keys__")
        and hasattr(expected, "__optional_keys__")
    )


def _required_markers() -> tuple[object, ...]:
    markers = tuple(
        marker
        for marker in (
            getattr(typing, "Required", None),
            getattr(typing, "NotRequired", None),
        )
        if marker is not None
    )
    try:
        from typing_extensions import NotRequired, Required
    except ImportError:
        return markers
    return (*markers, Required, NotRequired)


def _typed_dict_hints(expected: type) -> dict[str, object]:
    try:
        return get_type_hints(expected, include_extras=True)
    except (NameError, TypeError):
        module = sys.modules.get(expected.__module__)
        globalns = vars(module) if module is not None else {}
        localns = dict(vars(expected))
        resolved: dict[str, object] = {}
        for field, annotation in expected.__annotations__.items():
            try:
                resolved[field] = typing._eval_type(annotation, globalns, localns)
            except (NameError, TypeError):
                # Keep unresolved annotations intact so schema validation can
                # report them as invalid rather than losing other resolved fields.
                resolved[field] = annotation
        return resolved


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
    if get_origin(expected) in _required_markers():
        return get_args(expected)[0]
    return expected


def _union_args(expected: object) -> tuple[object, ...]:
    if isinstance(expected, tuple):
        return expected
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


def _is_json_scalar(value: object) -> bool:
    return (
        value is None
        or isinstance(value, (str, int, bool))
        or (isinstance(value, float) and math.isfinite(value))
    )


def _validate_type_spec(expected: object, path: str) -> None:
    expected = _unwrap_required(expected)
    if expected is Any:
        return
    if _is_typed_dict(expected):
        for field, nested in _typed_dict_hints(expected).items():
            _validate_type_spec(nested, f"{path}.{field}" if path else field)
    elif isinstance(expected, Mapping):
        for field, nested in expected.items():
            if not isinstance(field, str):
                raise TypeError("schema field names must be strings")
            _validate_type_spec(nested, f"{path}.{field}" if path else field)
    elif get_origin(expected) is list:
        item_args = get_args(expected)
        if len(item_args) != 1:
            raise TypeError(
                f"array schema for {path!r} must contain exactly one item schema"
            )
        _validate_type_spec(item_args[0], f"{path}[0]")
    elif isinstance(expected, list):
        if len(expected) != 1:
            raise TypeError(f"array schema for {path!r} must contain exactly one item schema")
        _validate_type_spec(expected[0], f"{path}[0]")
    elif _union_args(expected):
        for option in _union_args(expected):
            _validate_type_spec(option, path)
    elif _literal_args(expected):
        values = _literal_args(expected)
        if not all(_is_json_scalar(value) for value in values):
            raise TypeError(f"Literal schema for {path!r} must contain finite JSON scalar values")
    elif isinstance(expected, tuple):
        if not expected:
            raise TypeError(f"type union for {path!r} must contain at least one option")
        for option in expected:
            _validate_type_spec(option, path)
    elif _is_enum_type(expected):
        if not all(_is_json_scalar(member.value) for member in expected):
            raise TypeError(f"Enum schema for {path!r} must contain finite JSON scalar values")
    elif isinstance(expected, type):
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
    if expected is Any:
        return True
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
    if expected is Any:
        return "Any"
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
    union_options = _union_args(expected)
    has_structural_option = any(
        _is_typed_dict(option)
        or isinstance(option, Mapping)
        or get_origin(option) is list
        or isinstance(option, list)
        for option in union_options
    )
    if union_options and has_structural_option:
        branch_errors = [
            _collect_value_errors(value, option, path, strict)
            for option in union_options
        ]
        if any(not errors for errors in branch_errors):
            return []
        # Report the closest structural branch's errors. Scalar-only unions
        # continue through the normal type matcher to preserve combined errors.
        return min(branch_errors, key=len)
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
