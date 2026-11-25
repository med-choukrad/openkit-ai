import pytest

from openkit_ai import PromptManager, PromptTemplate


def test_add_and_get_prompt():
    manager = PromptManager()
    prompt = PromptTemplate("welcome", "Hello {name}.")

    manager.add(prompt)

    assert manager.get("welcome") is prompt
    assert "welcome" in manager
    assert len(manager) == 1


def test_rejects_duplicate_names_by_default():
    manager = PromptManager()
    manager.add(PromptTemplate("welcome", "Hello {name}."))

    with pytest.raises(ValueError, match="prompt already exists: welcome"):
        manager.add(PromptTemplate("welcome", "Hi {name}."))


def test_can_replace_existing_prompt():
    manager = PromptManager()
    manager.add(PromptTemplate("welcome", "Hello {name}."))
    replacement = PromptTemplate("welcome", "Hi {name}.")

    manager.add(replacement, replace=True)

    assert manager.get("welcome") is replacement


def test_names_preserve_insertion_order():
    manager = PromptManager()
    manager.add(PromptTemplate("first", "First"))
    manager.add(PromptTemplate("second", "Second"))

    assert manager.names == ("first", "second")


def test_renders_registered_prompt():
    manager = PromptManager()
    manager.add(PromptTemplate("summary", "Summarize {topic} for {audience}."))

    assert manager.render("summary", topic="AI", audience="developers") == (
        "Summarize AI for developers."
    )


def test_remove_returns_prompt_and_unregisters_it():
    manager = PromptManager()
    prompt = PromptTemplate("welcome", "Hello {name}.")
    manager.add(prompt)

    removed = manager.remove("welcome")

    assert removed is prompt
    assert "welcome" not in manager
    assert len(manager) == 0


def test_get_and_remove_raise_clear_error_for_unknown_name():
    manager = PromptManager()

    with pytest.raises(KeyError, match="unknown prompt: missing"):
        manager.get("missing")
    with pytest.raises(KeyError, match="unknown prompt: missing"):
        manager.remove("missing")


def test_add_requires_prompt_template():
    manager = PromptManager()

    with pytest.raises(TypeError, match="prompt must be a PromptTemplate"):
        manager.add("not a prompt")
