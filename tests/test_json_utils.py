import pytest

from openkit_ai import JSONResponseError, parse_json_response


def test_parses_plain_json_object():
    assert parse_json_response('{"ok": true, "count": 2}') == {"ok": True, "count": 2}


def test_parses_markdown_fenced_json():
    response = 'Here is the result:\n' + chr(96) * 3 + 'json\n{"items": [1, 2]}\n' + chr(96) * 3
    assert parse_json_response(response) == {"items": [1, 2]}


def test_parses_json_with_surrounding_text():
    assert parse_json_response('Result: {"answer": 42} Thanks!') == {"answer": 42}


def test_parses_array():
    assert parse_json_response('Output: [1, "two", 3]') == [1, "two", 3]


def test_raises_for_invalid_json():
    with pytest.raises(JSONResponseError):
        parse_json_response("There is no structured output here.")


def test_rejects_non_string_input():
    with pytest.raises(TypeError):
        parse_json_response({"already": "parsed"})

@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_rejects_nonstandard_json_numeric_constants(constant):
    with pytest.raises(JSONResponseError, match="No valid JSON object or array"):
        parse_json_response('{"value": ' + constant + '}')
