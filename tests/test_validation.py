import pytest

from openkit_ai import JSONValidationError, validate_json_response


def test_validates_required_fields_and_returns_object():
    result = validate_json_response(
        'Model output: {"name": "Ada", "age": 36, "active": true}',
        {"name": str, "age": int, "active": bool},
    )
    assert result == {"name": "Ada", "age": 36, "active": True}


def test_allows_additional_fields():
    result = validate_json_response(
        '{"name": "Ada", "role": "engineer"}',
        {"name": str},
    )
    assert result["role"] == "engineer"


def test_accepts_tuple_of_types():
    result = validate_json_response('{"count": 3}', {"count": (int, float)})
    assert result["count"] == 3


def test_reports_missing_fields():
    with pytest.raises(JSONValidationError, match="missing required field 'name'"):
        validate_json_response('{"age": 36}', {"name": str})


def test_reports_incorrect_types():
    with pytest.raises(JSONValidationError, match="field 'age' expected int, got str"):
        validate_json_response('{"age": "36"}', {"age": int})


def test_rejects_top_level_array():
    with pytest.raises(JSONValidationError, match="expected a JSON object"):
        validate_json_response('[1, 2, 3]', {"count": int})


def test_rejects_invalid_schema():
    with pytest.raises(TypeError, match="must be a type"):
        validate_json_response('{"age": 36}', {"age": "int"})


def test_rejects_non_mapping_schema():
    with pytest.raises(TypeError, match="schema must be a mapping"):
        validate_json_response('{"age": 36}', [("age", int)])


def test_validates_nested_object_fields():
    result = validate_json_response(
        '{"user": {"name": "Ada", "age": 36, "role": "engineer"}}',
        {"user": {"name": str, "age": int}},
    )
    assert result["user"]["name"] == "Ada"


def test_reports_nested_missing_field_with_path():
    with pytest.raises(JSONValidationError, match="missing required field 'user.email'"):
        validate_json_response(
            '{"user": {"name": "Ada"}}',
            {"user": {"name": str, "email": str}},
        )


def test_reports_nested_incorrect_type_with_path():
    with pytest.raises(JSONValidationError, match="field 'user.age' expected int, got str"):
        validate_json_response(
            '{"user": {"age": "36"}}',
            {"user": {"age": int}},
        )


def test_rejects_non_object_for_nested_schema():
    with pytest.raises(JSONValidationError, match="field 'user' expected object, got list"):
        validate_json_response('{"user": []}', {"user": {"name": str}})


def test_rejects_invalid_nested_schema():
    with pytest.raises(TypeError, match="user.age"):
        validate_json_response('{"user": {"age": 36}}', {"user": {"age": "int"}})
