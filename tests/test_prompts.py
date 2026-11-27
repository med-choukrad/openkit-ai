from types import SimpleNamespace

import pytest

from openkit_ai import PromptTemplate


def test_lists_template_variables_in_order_without_duplicates():
    prompt = PromptTemplate("welcome", "Hello {name}. You are using {tool}, {name}.")
    assert prompt.variables == ("name", "tool")


def test_renders_template():
    prompt = PromptTemplate("summary", "Summarize {text} for {audience}.")
    assert prompt.render(text="the report", audience="engineers") == (
        "Summarize the report for engineers."
    )


def test_rejects_missing_variables():
    prompt = PromptTemplate("summary", "Summarize {text}.")
    with pytest.raises(ValueError, match="missing variables: text"):
        prompt.render()


def test_rejects_unexpected_variables():
    prompt = PromptTemplate("summary", "Summarize {text}.")
    with pytest.raises(ValueError, match="unexpected variables: tex"):
        prompt.render(text="the report", tex="typo")


def test_rejects_empty_name_and_template():
    with pytest.raises(ValueError, match="name must not be empty"):
        PromptTemplate(" ", "Hello")
    with pytest.raises(ValueError, match="template must not be empty"):
        PromptTemplate("greeting", " ")


def test_rejects_malformed_braces():
    with pytest.raises(ValueError, match="invalid template syntax"):
        PromptTemplate("broken", "Hello {name")


@pytest.mark.parametrize("name", [None, 1, []])
def test_rejects_non_string_prompt_name(name):
    with pytest.raises(TypeError, match="name must be a string"):
        PromptTemplate(name, "Hello")


@pytest.mark.parametrize("template", [None, 1, []])
def test_rejects_non_string_prompt_template(template):
    with pytest.raises(TypeError, match="template must be a string"):
        PromptTemplate("greeting", template)


def test_includes_nested_format_spec_variables():
    prompt = PromptTemplate("aligned", "{value:>{width}}")
    assert prompt.variables == ("value", "width")
    assert prompt.render(value="ok", width=5) == "   ok"


def test_attribute_and_index_fields_use_their_root_variables():
    prompt = PromptTemplate("details", "{user.name}: {items[0]}")
    assert prompt.variables == ("user", "items")
    assert prompt.render(
        user=SimpleNamespace(name="Ada"),
        items=["first", "second"],
    ) == "Ada: first"


@pytest.mark.parametrize("template", ["{}", "{0}", "{1!r}", "{[0]}", "{0.name}"])
def test_rejects_positional_format_fields(template):
    with pytest.raises(ValueError, match="positional replacement fields are not supported"):
        PromptTemplate("positional", template)
