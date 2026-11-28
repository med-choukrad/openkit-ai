# Changelog

All notable changes to OpenKit AI are documented in this file.

## [0.12.0] - Unreleased

### Added
- JSON response parsing for objects and arrays, including model output wrapped in Markdown code fences or surrounding text.
- JSON response validation for nested objects and arrays, with strict type checking and optional rejection of undeclared fields.
- Support for optional values, `typing.Literal`, `Enum`, and `TypedDict` schemas, including `Required` and `NotRequired` keys.
- Synchronous and asynchronous retry helpers with exponential backoff, jitter, and validated retry options.
- Reusable prompt templates with required-variable inspection and strict rendering validation.
- In-memory prompt management and versioned JSON persistence.
- Regression coverage for malformed JSON, duplicate keys, validation edge cases, retry configuration, and prompt persistence.

### Compatibility
- Python 3.10, 3.11, 3.12, and 3.13.
- No runtime third-party dependencies.

### Release status
- This changelog entry is a release-preparation draft. It does not indicate that version 0.12.0 has been published to PyPI or tagged on GitHub.
