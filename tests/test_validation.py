from enum import Enum
from typing import Any, List, Literal

try:
    from typing import NotRequired, Required, TypedDict
except ImportError:  # Python 3.10
    from typing_extensions import NotRequired, Required, TypedDict

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


def test_rejects_unparameterized_typing_list_schema():
    with pytest.raises(TypeError, match="exactly one item schema"):
        validate_json_response('{"items": []}', {"items": List})



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

@pytest.mark.parametrize("nullable_type", [str | None, __import__("typing").Optional[str]])
def test_accepts_null_for_optional_field(nullable_type):
    result = validate_json_response('{"nickname": null}', {"nickname": nullable_type})
    assert result["nickname"] is None


def test_accepts_value_for_optional_field():
    assert validate_json_response(
        '{"nickname": "Ada"}', {"nickname": str | None}
    )["nickname"] == "Ada"


def test_rejects_wrong_type_for_optional_field():
    with pytest.raises(JSONValidationError, match="expected str or NoneType, got int"):
        validate_json_response('{"nickname": 42}', {"nickname": str | None})


def test_optional_type_works_in_nested_objects_and_arrays():
    result = validate_json_response(
        '{"user": {"nickname": null}, "nicknames": ["Ada", null]}',
        {"user": {"nickname": str | None}, "nicknames": [str | None]},
    )
    assert result["user"]["nickname"] is None
    assert result["nicknames"] == ["Ada", None]


def test_bool_is_not_accepted_by_optional_integer_type():
    with pytest.raises(JSONValidationError, match="expected int or NoneType, got bool"):
        validate_json_response('{"count": true}', {"count": int | None})



class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"


class Priority(Enum):
    LOW = 1
    HIGH = 3


@pytest.mark.parametrize("status", ["pending", "complete", "failed"])
def test_accepts_allowed_literal_values(status):
    result = validate_json_response(
        '{"status": "' + status + '"}',
        {"status": Literal["pending", "complete", "failed"]},
    )
    assert result["status"] == status


def test_rejects_value_outside_literal_choices():
    with pytest.raises(JSONValidationError, match=r"expected Literal\('pending', 'complete'\)"):
        validate_json_response(
            '{"status": "unknown"}',
            {"status": Literal["pending", "complete"]},
        )


def test_literal_matching_distinguishes_bool_from_int():
    with pytest.raises(JSONValidationError, match=r"expected Literal\(1,\), got bool"):
        validate_json_response('{"priority": true}', {"priority": Literal[1]})


def test_accepts_enum_member_values_from_json():
    result = validate_json_response(
        '{"status": "complete"}',
        {"status": TaskStatus},
    )
    assert result["status"] == "complete"


def test_rejects_value_not_defined_in_enum():
    with pytest.raises(JSONValidationError, match="expected TaskStatus, got str"):
        validate_json_response('{"status": "unknown"}', {"status": TaskStatus})


def test_accepts_integer_enum_values_from_json():
    result = validate_json_response('{"priority": 3}', {"priority": Priority})
    assert result["priority"] == 3


def test_enum_and_literal_work_in_nested_arrays_and_unions():
    result = validate_json_response(
        '{"statuses": ["pending", "complete"], "preferred": null}',
        {
            "statuses": [TaskStatus],
            "preferred": Literal["pending", "complete"] | None,
        },
    )
    assert result["statuses"] == ["pending", "complete"]
    assert result["preferred"] is None


def test_rejects_bool_for_integer_enum_value():
    with pytest.raises(JSONValidationError, match="expected Priority, got bool"):
        validate_json_response('{"priority": true}', {"priority": Priority})




class UserProfile(TypedDict):
    name: str
    age: int
    nickname: NotRequired[str]


class AdminProfile(UserProfile):
    role: Required[str]


def test_validates_typed_dict_schema():
    result = validate_json_response('{"name": "Ada", "age": 36}', UserProfile)
    assert result == {"name": "Ada", "age": 36}


def test_typed_dict_not_required_field_may_be_omitted():
    result = validate_json_response('{"name": "Ada", "age": 36}', UserProfile)
    assert "nickname" not in result


def test_typed_dict_not_required_field_is_validated_when_present():
    with pytest.raises(JSONValidationError, match="field 'nickname' expected str, got int"):
        validate_json_response('{"name": "Ada", "age": 36, "nickname": 7}', UserProfile)


def test_typed_dict_reports_missing_required_field():
    with pytest.raises(JSONValidationError, match="missing required field 'age'"):
        validate_json_response('{"name": "Ada"}', UserProfile)


def test_typed_dict_required_field_is_enforced():
    with pytest.raises(JSONValidationError, match="missing required field 'role'"):
        validate_json_response('{"name": "Ada", "age": 36}', AdminProfile)


def test_typed_dict_supports_nested_objects_and_arrays():
    class Team(TypedDict):
        members: list[UserProfile]

    result = validate_json_response(
        '{"members": [{"name": "Ada", "age": 36}]}', Team
    )
    assert result["members"][0]["name"] == "Ada"


def test_typed_dict_strict_mode_rejects_extra_fields():
    with pytest.raises(JSONValidationError, match="unexpected field 'nickname_extra'"):
        validate_json_response(
            '{"name": "Ada", "age": 36, "nickname_extra": "A"}',
            UserProfile,
            strict=True,
        )


def test_typed_dict_is_permissive_about_extra_fields_by_default():
    result = validate_json_response(
        '{"name": "Ada", "age": 36, "nickname_extra": "A"}', UserProfile
    )
    assert result["nickname_extra"] == "A"


def test_typed_dict_can_be_used_in_mapping_schema():
    result = validate_json_response(
        '{"user": {"name": "Ada", "age": 36}}', {"user": UserProfile}
    )
    assert result["user"]["name"] == "Ada"



class PostponedProfile(TypedDict):
    __annotations__ = {
        "name": "str",
        "nickname": "NotRequired[str]",
    }


class PostponedPartialProfile(TypedDict, total=False):
    __annotations__ = {
        "name": "Required[str]",
        "age": "NotRequired[int]",
    }


def test_typed_dict_resolves_postponed_required_markers():
    result = validate_json_response('{"name": "Ada"}', PostponedProfile)
    assert result == {"name": "Ada"}


def test_typed_dict_resolves_postponed_required_in_total_false_class():
    result = validate_json_response('{"name": "Ada"}', PostponedPartialProfile)
    assert result == {"name": "Ada"}


def test_typed_dict_requires_postponed_required_field():
    with pytest.raises(JSONValidationError, match="missing required field 'name'"):
        validate_json_response("{}", PostponedPartialProfile)


def test_union_supports_nested_mapping_schema():
    result = validate_json_response(
        '{"payload": {"name": "Ada"}}',
        {"payload": ({"name": str}, type(None))},
    )
    assert result["payload"]["name"] == "Ada"


def test_union_supports_typed_dict_schema():
    result = validate_json_response(
        '{"user": {"name": "Ada", "age": 36}}',
        {"user": (UserProfile, type(None))},
    )
    assert result["user"]["name"] == "Ada"


def test_union_reports_structural_branch_error():
    with pytest.raises(JSONValidationError, match="missing required field 'payload.name'"):
        validate_json_response(
            '{"payload": {"age": 36}}',
            {"payload": ({"name": str}, type(None))},
        )


def test_any_accepts_arbitrary_json_values():
    result = validate_json_response(
        '{"text": "hello", "count": 3, "active": true, "items": [1, null]}',
        {
            "text": Any,
            "count": __import__("typing").Any,
            "active": __import__("typing").Any,
            "items": [__import__("typing").Any],
        },
    )
    assert result == {
        "text": "hello",
        "count": 3,
        "active": True,
        "items": [1, None],
    }
