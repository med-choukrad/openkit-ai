import json

import pytest

from openkit_ai import PromptManager, PromptTemplate


def test_save_and_load_round_trip(tmp_path):
    manager = PromptManager()
    manager.add(PromptTemplate("greeting", "Hello {name}!"))
    manager.add(PromptTemplate("summary", "Summarize {text}."))

    path = tmp_path / "prompts.json"
    manager.save(path)
    restored = PromptManager.load(path)

    assert restored.names == ("greeting", "summary")
    assert restored.render("greeting", name="Ada") == "Hello Ada!"
    assert restored.get("summary").template == "Summarize {text}."


def test_save_preserves_unicode(tmp_path):
    manager = PromptManager()
    manager.add(PromptTemplate("arabic", "مرحبا {name}"))

    path = tmp_path / "prompts.json"
    manager.save(path)

    assert "مرحبا" in path.read_text(encoding="utf-8")
    assert PromptManager.load(path).get("arabic").template == "مرحبا {name}"


def test_load_rejects_invalid_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid prompt file JSON"):
        PromptManager.load(path)


@pytest.mark.parametrize("data", [[], "text", None])
def test_load_rejects_non_object_root(tmp_path, data):
    path = tmp_path / "prompts.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(TypeError, match="expected a JSON object"):
        PromptManager.load(path)


def test_load_rejects_unsupported_version(tmp_path):
    path = tmp_path / "prompts.json"
    path.write_text(json.dumps({"version": 99, "prompts": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported prompt file version"):
        PromptManager.load(path)


def test_load_rejects_invalid_prompt_entries(tmp_path):
    path = tmp_path / "prompts.json"
    path.write_text(
        json.dumps({"version": 1, "prompts": [{"name": "bad", "template": 42}]}),
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match="name.*template.*must be strings"):
        PromptManager.load(path)


def test_load_rejects_duplicate_prompt_names(tmp_path):
    path = tmp_path / "prompts.json"
    path.write_text(
        json.dumps({
            "version": 1,
            "prompts": [
                {"name": "same", "template": "One"},
                {"name": "same", "template": "Two"},
            ],
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="prompt already exists: same"):
        PromptManager.load(path)


def test_load_rejects_invalid_template(tmp_path):
    path = tmp_path / "prompts.json"
    path.write_text(
        json.dumps({"version": 1, "prompts": [{"name": "broken", "template": "Hi {"}]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid template syntax"):
        PromptManager.load(path)


def test_load_rejects_boolean_format_version(tmp_path):
    path = tmp_path / "prompts.json"
    path.write_text(
        json.dumps({"version": True, "prompts": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported prompt file version"):
        PromptManager.load(path)
