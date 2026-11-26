# OpenKit AI

Small, dependency-free utilities for developers building AI-powered Python applications.

OpenKit AI currently provides five practical building blocks:

- **JSON response parsing** — extract a valid JSON object or array from plain model output, Markdown code fences, or text with surrounding explanation.
- **Structured output validation** — check that a model response is a JSON object containing required fields with the expected Python types, including nested objects and arrays.
- **Retry with exponential backoff** — retry transient failures such as timeouts and connection errors in both synchronous and asynchronous code.
- **Prompt templates** — define reusable prompts, inspect their required variables, and render them with strict input validation.
- **Prompt management** — store, retrieve, replace, render, remove, and save or load named prompt templates using JSON.

The project is vendor-neutral. It does not call an AI service, collect data, or require API keys at runtime.

## Installation

Python 3.10 or newer is required.

```bash
python -m pip install openkit-ai
```

## Quick start

```python
from openkit_ai import (
    PromptManager,
    PromptTemplate,
    async_call_with_retry,
    call_with_retry,
    parse_json_response,
    validate_json_response,
)

prompts = PromptManager()
prompts.add(PromptTemplate("summary", "Summarize {text} for {audience}."))
rendered = prompts.render("summary", text="the report", audience="engineers")
print(rendered)

data = parse_json_response('Model output: {"sentiment": "positive"}')
print(data["sentiment"])

profile = validate_json_response(
    'Model output: {"name": "Ada", "age": 36}',
    {"name": str, "age": int},
)
print(profile["name"])

result = call_with_retry(
    lambda: make_your_api_call(),
    retry_on=(TimeoutError, ConnectionError),
    max_attempts=3,
)

# For async functions, use async_call_with_retry inside an async function:
# result = await async_call_with_retry(make_your_async_api_call)
```

### Managing prompts

`PromptManager` stores `PromptTemplate` objects by name. Duplicate names are rejected unless you explicitly pass `replace=True`. The manager keeps prompts in memory by default. Use `save()` and `load()` to persist them in a versioned JSON file; this does not send prompts to an AI provider.

```python
manager = PromptManager()
manager.add(PromptTemplate("greeting", "Hello {name}!"))

print(manager.names)  # ("greeting",)
print(manager.render("greeting", name="Ada"))

manager.add(PromptTemplate("greeting", "Hi {name}!"), replace=True)
manager.save("prompts.json")
restored = PromptManager.load("prompts.json")
print(restored.render("greeting", name="Ada"))
manager.remove("greeting")
```

### JSON response validation

The validation schema maps required field names to Python types. Nested mappings validate fields inside objects, and a one-item list schema validates every item in a JSON array:

```python
data = validate_json_response(
    '{"users": [{"name": "Ada", "age": 36}], "tags": ["python", "ai"]}',
    {
        "users": [{"name": str, "age": int}],
        "tags": [str],
    },
)
```

Use `[str]` for an array of strings, `[{"name": str}]` for an array of objects, and nested forms such as `[[int]]` for arrays of arrays. Each list schema must contain exactly one item schema. An empty array in the response is valid. Existing schemas using plain types, tuples of types, and nested mappings continue to work. Additional object fields are allowed at every level. Validation errors include array indexes, such as `users[1].age`. JSON booleans are not accepted as integers (even though Python treats `bool` as a subclass of `int`); use `bool` explicitly in the schema when a boolean is expected. By default, extra object fields are allowed. Pass `strict=True` to reject undeclared fields at the top level and inside nested objects or arrays of objects:


```python
validate_json_response(
    '{"name": "Ada", "role": "engineer"}',
    {"name": str},
    strict=True,
)
```

A `JSONValidationError` is raised when required fields are missing or have the wrong type, an array or object has the wrong shape, an undeclared field is found in strict mode, or the top-level JSON value is not an object.

See the [examples](examples/) directory for complete usage examples.

Optional fields can accept JSON `null` by using `str | None` or `Optional[str]` in the schema. This also works inside nested objects and arrays:

```python
from typing import Optional

validate_json_response(
    '{"name": "Ada", "nickname": null}',
    {"name": str, "nickname": Optional[str]},
)
```

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
```

## Project status

OpenKit AI is in early development. The public API may evolve before the first stable release. Bug reports, focused feature proposals, documentation improvements, and tested pull requests are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

MIT. See [LICENSE](LICENSE).
