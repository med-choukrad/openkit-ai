"""Reusable, validated prompt templates for AI applications."""

from __future__ import annotations

from dataclasses import dataclass
from string import Formatter


def _root_field_name(field_name: str) -> str:
    """Return the keyword argument needed to resolve a format field."""
    end = len(field_name)
    for separator in (".", "["):
        position = field_name.find(separator)
        if position != -1:
            end = min(end, position)
    return field_name[:end]


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
            parsed = list(Formatter().parse(self.template))
            self._validate_named_fields(parsed)
        except ValueError as error:
            raise ValueError(f"invalid template syntax: {error}") from error

    @staticmethod
    def _validate_named_fields(parsed: list[tuple[str, str | None, str | None, str | None]]) -> None:
        for _, field_name, format_spec, _ in parsed:
            if field_name is not None and (
                not _root_field_name(field_name)
                or _root_field_name(field_name).isdecimal()
            ):
                raise ValueError(
                    "positional replacement fields are not supported; use named fields"
                )
            if format_spec:
                nested = list(Formatter().parse(format_spec))
                PromptTemplate._validate_named_fields(nested)

    @property
    def variables(self) -> tuple[str, ...]:
        """Return unique keyword variables in first-seen order."""
        fields: list[str] = []

        def collect(parsed: list[tuple[str, str | None, str | None, str | None]]) -> None:
            for _, field_name, format_spec, _ in parsed:
                if field_name is not None:
                    root_name = _root_field_name(field_name)
                    if root_name not in fields:
                        fields.append(root_name)
                if format_spec:
                    collect(list(Formatter().parse(format_spec)))

        collect(list(Formatter().parse(self.template)))
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
