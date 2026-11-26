"""Helpers for parsing JSON embedded in AI model responses."""

from __future__ import annotations

import json
from typing import Any


class JSONResponseError(ValueError):
    """Raised when a response does not contain a valid JSON object or array."""


def parse_json_response(response: str) -> Any:
    """Parse the first JSON object or array found in a text response.

    Accepts plain JSON, Markdown code fences, and surrounding explanatory text.
    Only JSON objects and arrays are returned.
    """
    if not isinstance(response, str):
        raise TypeError("response must be a string")

    text = response.strip()
    if text.startswith(chr(96) * 3):
        lines = text.splitlines()
        if lines and lines[0].lstrip().startswith(chr(96) * 3):
            lines = lines[1:]
        if lines and lines[-1].strip() == chr(96) * 3:
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    def reject_nonstandard_constant(value: str) -> None:
        raise ValueError(f"invalid JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    decoder = json.JSONDecoder(
        parse_constant=reject_nonstandard_constant,
        object_pairs_hook=reject_duplicate_keys,
    )
    index = 0
    while index < len(text):
        character = text[index]
        if character == '"':
            # Ignore JSON-looking text inside quoted explanatory prose.
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                elif text[index] == '"':
                    index += 1
                    break
                else:
                    index += 1
            continue

        if character in "[{":
            try:
                value, _ = decoder.raw_decode(text, index)
            except (json.JSONDecodeError, ValueError):
                index += 1
                continue
            if isinstance(value, (dict, list)):
                return value
        index += 1

    raise JSONResponseError("No valid JSON object or array found in response")
