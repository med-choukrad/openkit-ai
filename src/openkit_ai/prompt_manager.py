"""In-memory management for reusable prompt templates."""

from __future__ import annotations

from .prompts import PromptTemplate


class PromptManager:
    """Store, retrieve, render, and remove named prompt templates."""

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

    def render(self, name: str, **values: object) -> str:
        """Render a registered prompt using its validated template."""
        return self.get(name).render(**values)

    def __len__(self) -> int:
        return len(self._templates)

    def __contains__(self, name: object) -> bool:
        return name in self._templates
