import pytest

from openkit_ai import JSONValidationError, validate_json_response


def test_validates_required_fields_and_returns_object():
    result = validate_json_response(
        'Model output: {"name": "Ada", "age": 36, "active": true}',
        {"name": str, "age": int, "active": bool},
    )
    assert result == {"name": "Ada", "age": 36, "active": True}


def test_allows_additional_fields():
    result = validate_json_response('{"name": "Ada", "role": "engineer"}', {"name": str})
    assert result["role"] == "engineer"


def test_accepts_tuple_of_types():
    assert validate_json_response('{"count": 3}', {"count": (int, float)})["count"] == 3


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
        validate_json_response('{"user": {"name": "Ada"}}', {"user": {"name": str, "email": str}})


def test_reports_nested_incorrect_type_with_path():
    with pytest.raises(JSONValidationError, match="field 'user.age' expected int, got str"):
        validate_json_response('{"user": {"age": "36"}}', {"user": {"age": int}})


def test_rejects_non_object_for_nested_schema():
    with pytest.raises(JSONValidationError, match="field 'user' expected object, got list"):
        validate_json_response('{"user": []}', {"user": {"name": str}})


def test_rejects_invalid_nested_schema():
    with pytest.raises(TypeError, match="user.age"):
        validate_json_response('{"user": {"age": 36}}', {"user": {"age": "int"}})


def test_validates_array_of_strings():
    assert validate_json_response('{"tags": ["ai", "python"]}', {"tags": [str]})["tags"] == ["ai", "python"]


def test_accepts_empty_array():
    assert validate_json_response('{"tags": []}', {"tags": [str]}) == {"tags": []}


def test_rejects_non_array_value():
    with pytest.raises(JSONValidationError, match="field 'tags' expected array, got str"):
        validate_json_response('{"tags": "ai"}', {"tags": [str]})


def test_reports_array_item_type_with_index():
    with pytest.raises(JSONValidationError, match=r"field 'tags\[1\]' expected str, got int"):
        validate_json_response('{"tags": ["ai", 2]}', {"tags": [str]})


def test_validates_array_of_objects():
    result = validate_json_response(
        '{"users": [{"name": "Ada", "age": 36}, {"name": "Lin", "age": 28}]}',
        {"users": [{"name": str, "age": int}]},
    )
    assert len(result["users"]) == 2


def test_reports_array_object_error_with_index_and_field():
    with pytest.raises(JSONValidationError, match=r"field 'users\[1\]\.age' expected int, got str"):
        validate_json_response(
            '{"users": [{"name": "Ada", "age": 36}, {"name": "Lin", "age": "28"}]}',
            {"users": [{"name": str, "age": int}]},
        )


def test_reports_missing_array_object_field_with_index():
    with pytest.raises(JSONValidationError, match=r"missing required field 'users\[0\]\.age'"):
        validate_json_response('{"users": [{"name": "Ada"}]}', {"users": [{"name": str, "age": int}]})


def test_validates_nested_arrays():
    assert validate_json_response('{"matrix": [[1, 2], [3]]}', {"matrix": [[int]]})["matrix"] == [[1, 2], [3]]


@pytest.mark.parametrize("invalid_schema", [[], [str, int]])
def test_rejects_array_schema_without_exactly_one_item_schema(invalid_schema):
    with pytest.raises(TypeError, match="exactly one item schema"):
        validate_json_response('{"items": []}', {"items": invalid_schema})



def test_rejects_boolean_for_integer_field():
    with pytest.raises(JSONValidationError, match="field 'count' expected int, got bool"):
        validate_json_response('{"count": true}', {"count": int})


def test_accepts_boolean_for_explicit_boolean_field():
    assert validate_json_response('{"active": true}', {"active": bool})["active"] is True


def test_rejects_boolean_in_integer_or_float_tuple():
    with pytest.raises(JSONValidationError, match="field 'value' expected int or float, got bool"):
        validate_json_response('{"value": false}', {"value": (int, float)})


def test_accepts_boolean_when_explicitly_in_type_tuple():
    assert validate_json_response('{"value": true}', {"value": (int, bool)})["value"] is True


def test_rejects_boolean_in_integer_array():
    with pytest.raises(JSONValidationError, match=r"field 'values\[1\]' expected int, got bool"):
        validate_json_response('{"values": [1, true]}', {"values": [int]})


def test_strict_mode_rejects_unexpected_top_level_fields():
    with pytest.raises(JSONValidationError, match="unexpected field 'role'"):
        validate_json_response('{"name": "Ada", "role": "engineer"}', {"name": str}, strict=True)


def test_strict_mode_rejects_unexpected_nested_fields():
    with pytest.raises(JSONValidationError, match="unexpected field 'user.role'"):
        validate_json_response(
            '{"user": {"name": "Ada", "role": "engineer"}}',
            {"user": {"name": str}},
            strict=True,
        )


def test_strict_mode_rejects_unexpected_fields_in_array_objects():
    with pytest.raises(JSONValidationError, match=r"unexpected field 'users\[0\]\.role'"):
        validate_json_response(
            '{"users": [{"name": "Ada", "role": "engineer"}]}',
            {"users": [{"name": str}]},
            strict=True,
        )


def test_default_mode_continues_to_allow_unexpected_fields():
    result = validate_json_response(
        '{"user": {"name": "Ada", "role": "engineer"}}',
        {"user": {"name": str}},
    )
    assert result["user"]["role"] == "engineer"


def test_strict_mode_requires_boolean_argument():
    with pytest.raises(TypeError, match="strict must be a bool"):
        validate_json_response('{"name": "Ada"}', {"name": str}, strict="yes")
