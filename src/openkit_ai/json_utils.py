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

    decoder = json.JSONDecoder(parse_constant=reject_nonstandard_constant)
    for index, character in enumerate(text):
        if character not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(value, (dict, list)):
            return value

    raise JSONResponseError("No valid JSON object or array found in response")
