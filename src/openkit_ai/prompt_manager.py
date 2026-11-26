"""In-memory management and JSON persistence for prompt templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .prompts import PromptTemplate


class PromptManager:
    """Store, retrieve, render, and persist named prompt templates."""

    _FORMAT_VERSION = 1

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def add(self, prompt: PromptTemplate, *, replace: bool = False) -> None:
        """Register a prompt; reject duplicate names unless replace=True."""
        if not isinstance(prompt, PromptTemplate):
            raise TypeError("prompt must be a PromptTemplate")
        if prompt.name in self._templates and not replace:
            raise ValueError(f"prompt already exists: {prompt.name}")
        self._templates[prompt.name] = prompt

    def get(self, name: str) -> PromptTemplate:
        """Return a registered prompt by name."""
        try:
            return self._templates[name]
        except KeyError:
            raise KeyError(f"unknown prompt: {name}") from None

    def remove(self, name: str) -> PromptTemplate:
        """Remove and return a registered prompt."""
        try:
            return self._templates.pop(name)
        except KeyError:
            raise KeyError(f"unknown prompt: {name}") from None

    @property
    def names(self) -> tuple[str, ...]:
        """Return registered prompt names in insertion order."""
        return tuple(self._templates)

    def render(self, prompt_name: str, **values: object) -> str:
        """Render a registered prompt using its validated template."""
        return self.get(prompt_name).render(**values)

    def save(self, path: str | Path) -> None:
        """Save all prompts to a UTF-8 JSON file."""
        data = {
            "version": self._FORMAT_VERSION,
            "prompts": [
                {"name": prompt.name, "template": prompt.template}
                for prompt in self._templates.values()
            ],
        }
        destination = Path(path)
        destination.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> PromptManager:
        """Load prompts from a JSON file created by save()."""
        source = Path(path)
        try:
            data: Any = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid prompt file JSON: {error}") from error

        if not isinstance(data, dict):
            raise TypeError("invalid prompt file: expected a JSON object")
        version = data.get("version")
        if type(version) is not int or version != cls._FORMAT_VERSION:
            raise ValueError(f"unsupported prompt file version: {version!r}")
        prompts = data.get("prompts")
        if not isinstance(prompts, list):
            raise TypeError("invalid prompt file: 'prompts' must be a list")

        manager = cls()
        for index, item in enumerate(prompts):
            if not isinstance(item, dict):
                raise TypeError(f"invalid prompt at index {index}: expected an object")
            name = item.get("name")
            template = item.get("template")
            if not isinstance(name, str) or not isinstance(template, str):
                raise TypeError(
                    f"invalid prompt at index {index}: 'name' and 'template' "
                    "must be strings"
                )
            try:
                manager.add(PromptTemplate(name, template))
            except (TypeError, ValueError) as error:
                raise ValueError(f"invalid prompt at index {index}: {error}") from error
        return manager

    def __len__(self) -> int:
        return len(self._templates)

    def __contains__(self, name: object) -> bool:
        return name in self._templates
