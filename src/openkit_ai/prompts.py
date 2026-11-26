"""Reusable, validated prompt templates for AI applications."""

from __future__ import annotations

from dataclasses import dataclass
from string import Formatter


@dataclass(frozen=True)
class PromptTemplate:
    """A named string template with explicit, validated input variables."""

    name: str
    template: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not isinstance(self.template, str):
            raise TypeError("template must be a string")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if not self.template.strip():
            raise ValueError("template must not be empty")
        try:
            list(Formatter().parse(self.template))
        except ValueError as error:
            raise ValueError(f"invalid template syntax: {error}") from error

    @property
    def variables(self) -> tuple[str, ...]:
        """Return unique replacement field names in first-seen order."""
        fields: list[str] = []
        for _, field_name, _, _ in Formatter().parse(self.template):
            if field_name is not None and field_name not in fields:
                fields.append(field_name)
        return tuple(fields)

    def render(self, **values: object) -> str:
        """Render the template, requiring exactly the declared variables."""
        required = set(self.variables)
        supplied = set(values)
        missing = sorted(required - supplied)
        unexpected = sorted(supplied - required)
        if missing or unexpected:
            details = []
            if missing:
                details.append(f"missing variables: {', '.join(missing)}")
            if unexpected:
                details.append(f"unexpected variables: {', '.join(unexpected)}")
            raise ValueError("; ".join(details))
        return self.template.format(**values)
