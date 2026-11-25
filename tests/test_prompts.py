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
